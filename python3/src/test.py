import MySQLdb

conn = MySQLdb.connect(host="localhost", port=6001, user="dump", passwd="111", db="mo_cloud")
cursor = conn.cursor()
cursor.execute("create database if not exists ai_doc;")
cursor.execute('''
    create table if not exists MODocEmbedding(
    `id` bigint auto_increment primary key comment 'ID',
    `doc_embedding_vector` vecf64(1536) not null comment 'doc embedding vector',
    `text_chunk` text not null comment 'chunk text',
    `payload` text not null comment 'payload data'
    );
''')
conn.commit()



cursor.close()
conn.close()