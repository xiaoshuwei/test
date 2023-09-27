use mo_cloud;
show tables;

create database if not exists ai_doc;
create table if not exists mo_doc_embedding(
   `id` varchar(256) not null comment 'uuid primary key with id',
   `doc_embedding_vector` vecf64(1536) not null comment 'doc embedding vector',
   `text_chunk` text not null comment 'chunk text',
   `payload` text not null comment 'payload data',
   primary key (`id`)
);



show databases;
use ai_doc;
show tables;
show create table ai_doc.mo_doc_embedding;

CREATE TABLE `mo_doc_embedding` ( 
   `id` VARCHAR(256) NOT NULL COMMENT 'uuid primary key with id', 
   `doc_embedding_vector` VECTOR DOUBLE(1536) NOT NULL COMMENT 'doc embedding vector', 
   `text_chunk` TEXT NOT NULL COMMENT 'chunk text', 
   `payload` TEXT NOT NULL COMMENT 'payload data', 
   PRIMARY KEY (`id`) 
   );