"""Wrapper around Matrixone vector database."""
import uuid
from operator import itemgetter
from typing import Any, Callable, Iterable, List, Optional, Tuple

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.utils import get_from_dict_or_env
from langchain.vectorstores import VectorStore
from langchain.vectorstores.utils import maximal_marginal_relevance
from langchain.math_utils import Matrix
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import ColumnClause
from typing import List
from sqlalchemy import String, TEXT, create_engine, select, Table, Column, text, delete
import sqlalchemy.types as types
from sqlalchemy.orm import registry
import json
import uuid
import numpy as np

class MODoubleVector(types.UserDefinedType):
    impl = types.TEXT

    cache_ok = True

    def __init__(self, precision:int = None):
        if precision == None :
            raise ValueError(
                "precision is None. "
                "Please input precision."
            )
        self.precision = precision

    def get_col_spec(self, **kw):
        return "vecf64(%s)" % self.precision
    
    def bind_processor(self, dialect):
        def process(value):
            return json.dumps(value,separators=(',',':'))
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return json.loads(value)
        return process

class MODocEmbedding:
    def __init__(self, id=None, payload=None, doc_embedding_vector=None):
        if id == None:
            id = uuid.uuid4().hex
        self.id = id
        self.doc_embedding_vector = doc_embedding_vector
        self.payload = payload
    @classmethod
    def _to_vector_str(cls, vector:List[float]) -> str:
        return json.dumps(vector,separators=(',',':'))

class MODocEmbeddingWithScore(MODocEmbedding):
    def __init__(self, id=None, payload=None, doc_embedding_vector=None):
        super.__init__(id,payload,doc_embedding_vector)
        self.score = 0

class Matrixone(VectorStore):
    """
    Wrapper around Matrixone vector database.
    Example:
        .. code-block:: python
            from langchain import Matrixone
            conn = MySQLdb.connect(host="127.0.0.1", port=6001, user="user", passwd="pwd", db="database_name")
            table_name = "table_name"
            column_name = "embedding_column_name"
            MO = Matrixone(conn, table_name, column_name, embedding)
    """

    def __init__(self, 
                 table_name: str, 
                 embedding: Embeddings, 
                 host:str, 
                 user:str, 
                 password:str, 
                 dbname:str,
                 port:str = 6001):
        """Initialize with necessary components."""
        
        self.table_name = table_name
        self.embedding = embedding
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dbname = dbname
        connectionSQL = "mysql+pymysql://%s:%s@%s:%s/%s" % (user,password,host,port,dbname)
        self.engine = create_engine(connectionSQL, echo=True)

    def _new_mo_doc_embedding_table_and_registry(self,dimensions):
        mapper_registry = registry()
        table = Table(
            self.table_name,
            mapper_registry.metadata,
            Column("id",String(256),primary_key=True),
            Column("payload",TEXT,nullable=False),
            Column("doc_embedding_vector",MODoubleVector(dimensions),nullable=False)
        )
        mapper_registry.metadata.create_all(bind=self.engine)
        mapper_registry.map_imperatively(MODocEmbedding,table,properties={
            'id': table.c.id,
            'payload': table.c.payload,
            'doc_embedding_vector': table.c.doc_embedding_vector,
        })

    def _get_session(self):
        Session = sessionmaker(bind=self.engine)
        return Session()

    def add_texts(
        self, texts: Iterable[str], metadatas: Optional[List[dict]] = None
    ) -> List[str]:
        """Run more texts through the embeddings and add to the vectorstore.
        Args:
            texts: Iterable of strings to add to the vectorstore.
            metadatas: Optional list of metadatas associated with the texts.
        Returns:
            List of ids from adding the texts into the vectorstore.
        """

        payloads = self._build_payloads(texts=texts,metadatas=metadatas)
        
        vectors = self.embedding.embed_documents(texts=texts)

        if len(vectors) <= 0:
            return []
        dimensions = len(vectors[0])

        self._new_mo_doc_embedding_table_and_registry(dimensions)

        session = self._get_session()

        docs = []
        ids = []
        for i in range(len(texts)):
            id = uuid.uuid4().hex
            docs.append(MODocEmbedding(id=id,payload=json.dumps(payloads[i]),doc_embedding_vector=vectors[i]))
            ids.append(id)
        
        session.add_all(docs)

        session.commit()

        session.close()

        return ids

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Return docs most similar to query.
        Args:
            query: Text to look up documents similar to.
            k: Number of Documents to return. Defaults to 4.
        Returns:
            List of Documents most similar to the query.
        """
        results = self.similarity_search_with_score(query, k)
        return list(map(itemgetter(0), results))

    def similarity_search_by_vector(
        self, embedding: List[float], k: int = 4, **kwargs: Any
    ) -> List[Document]:
        """Return docs most similar to embedding vector.

        Args:
            embedding: Embedding to look up documents similar to.
            k: Number of Documents to return. Defaults to 4.

        Returns:
            List of Documents most similar to the query vector.
        """
        results = self.similarity_search_by_vector_with_score(embedding=embedding, k=k)
        return list(map(itemgetter(0), results))

    def similarity_search_with_score(
        self, query: str, k: int = 4
    ) -> List[Tuple[Document, float]]:
        """Return docs most similar to query.
        Args:
            query: Text to look up documents similar to.
            k: Number of Documents to return. Defaults to 4.
        Returns:
            List of Documents most similar to the query and score for each
        """
        return self.similarity_search_by_vector_with_score(embedding=self.embedding.embed_query(query),k=k)

    def similarity_search_by_vector_with_score(
        self, embedding: List[float], k: int = 4
    ) -> List[Tuple[Document, float]]:
        session = self._get_session()

        sql = text("SELECT *,cosine_similarity(doc_embedding_vector, :embedding_str) as score FROM %s ORDER BY score LIMIT :limit_count ;" % (self.table_name))
        results = session.execute(sql,{'embedding_str':self._to_vector_str(embedding),'limit_count':k})

        session.commit()
        session.close()

        return [
            (
                self._document_from_payload(result.payload),
                result.score,
            )
            for result in results.mappings().all()
        ]

    def max_marginal_relevance_search(
        self,
        query: str,
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        **kwargs: Any,
    ) -> List[Document]:
        """Return docs selected using the maximal marginal relevance.

        Maximal marginal relevance optimizes for similarity to query AND diversity
        among selected documents.

        Args:
            query: Text to look up documents similar to.
            k: Number of Documents to return. Defaults to 4.
            fetch_k: Number of Documents to fetch to pass to MMR algorithm.
                     Defaults to 20.
            lambda_mult: Number between 0 and 1 that determines the degree
                        of diversity among the results with 0 corresponding
                        to maximum diversity and 1 to minimum diversity.
                        Defaults to 0.5.
        Returns:
            List of Documents selected by maximal marginal relevance.
        """
        query_embedding = self.embedding.embed_query(query)
        return self.max_marginal_relevance_search_by_vector(
            query_embedding, k, fetch_k, lambda_mult, **kwargs
        )
    
    def max_marginal_relevance_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        **kwargs: Any,
    ) -> List[Document]:
        """Return docs selected using the maximal marginal relevance.

        Maximal marginal relevance optimizes for similarity to query AND diversity
        among selected documents.

        Args:
            embedding: Embedding to look up documents similar to.
            k: Number of Documents to return. Defaults to 4.
            fetch_k: Number of Documents to fetch to pass to MMR algorithm.
            lambda_mult: Number between 0 and 1 that determines the degree
                        of diversity among the results with 0 corresponding
                        to maximum diversity and 1 to minimum diversity.
                        Defaults to 0.5.
        Returns:
            List of Documents selected by maximal marginal relevance.
        """
        results = self.max_marginal_relevance_search_with_score_by_vector(
            embedding=embedding, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult, **kwargs
        )
        return list(map(itemgetter(0), results))

    def max_marginal_relevance_search_with_score_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return docs selected using the maximal marginal relevance.
        Maximal marginal relevance optimizes for similarity to query AND diversity
        among selected documents.
        Args:
            query: Text to look up documents similar to.
            k: Number of Documents to return. Defaults to 4.
            fetch_k: Number of Documents to fetch to pass to MMR algorithm.
                     Defaults to 20.
            lambda_mult: Number between 0 and 1 that determines the degree
                        of diversity among the results with 0 corresponding
                        to maximum diversity and 1 to minimum diversity.
                        Defaults to 0.5.
        Returns:
            List of Documents selected by maximal marginal relevance and distance for
            each.
        """
        session = self._get_session()

        sql = text("SELECT *,cosine_similarity(doc_embedding_vector, :embedding_str) as score FROM %s ORDER BY score LIMIT :limit_count ;" % (self.table_name))
        results = session.execute(sql,{'embedding_str':self._to_vector_str(embedding),'limit_count':fetch_k})

        session.commit()
        session.close()

        results_maps = results.mappings().all()
        embeddings = [
            self._str_to_vector(result.doc_embedding_vector) for result in results_maps
        ]

        mmr_selected = maximal_marginal_relevance(
            np.array(embedding), embeddings, k=k, lambda_mult=lambda_mult
        )

        return [
            (
                self._document_from_payload(results_maps[i].payload),
                results_maps[i].score,
            )
            for i in mmr_selected
        ]
    
    @property
    def embeddings(self) -> Optional[Embeddings]:
        return self._embeddings
    
    def delete(self, ids: Optional[List[str]] = None, **kwargs: Any) -> Optional[bool]:
        """Delete by vector ID or other criteria.

        Args:
            ids: List of ids to delete.
            **kwargs: Other keyword arguments that subclasses might use.

        Returns:
            Optional[bool]: True if deletion is successful,
            False otherwise, None if not implemented.
        """
        session = self._get_session()

        docs = session.query(MODocEmbedding).filter(MODocEmbedding.id.in_(ids))
        for doc in docs:
            session.delete(doc)
        
        session.commit()

        session.close()

        return True
    
    def _select_relevance_score_fn(self) -> Callable[[float], float]:
        return self._cosine_relevance_score_fn

    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        user: str,
        password: str,
        dbname: str,
        metadatas: List[dict] = None,
        host: str = '127.0.0.1',
        port: int = 6001,
        table_name: str = 'mo_doc_vector',
        **kwargs: Any,
    ) -> "Matrixone":
        """Construct Matrixone wrapper from raw documents.
        This is a user friendly interface that:
            1. Embeds documents.
            2. Initializes the Matrixone database
        This is intended to be a quick way to get started.
        Example:
            .. code-block:: python
                from langchain import Matrixone
                from langchain.embeddings import OpenAIEmbeddings
                embeddings = OpenAIEmbeddings()
                mo = Matrixone.from_texts(texts=texts,embedding=embedding,user=user,password=password,dbname=dbname)
        """
        mo = Matrixone(table_name=table_name,embedding=embedding,host=host,port=port,user=user,password=password,dbname=dbname)
        mo.add_texts(texts=texts,metadatas=metadatas)
        return mo

    @classmethod
    def _build_payloads(
        cls, texts: Iterable[str], metadatas: Optional[List[dict]]
    ) -> List[dict]:
        return [
            {
                "page_content": text,
                "metadata": metadatas[i] if metadatas is not None else None,
            }
            for i, text in enumerate(texts)
        ]

    @classmethod
    def _document_from_payload(cls, payload: str) -> Document:
        payload_map = json.loads(payload)
        return Document(
            page_content=payload_map["page_content"],
            metadata=payload_map["metadata"],
        )

    @classmethod
    def _to_vector_str(cls, vector:List[float]) -> str:
        return json.dumps(vector,separators=(',',':'))
    @classmethod
    def _str_to_vector(cls, vector_str:str) -> List[float]:
        return json.loads(vector_str)