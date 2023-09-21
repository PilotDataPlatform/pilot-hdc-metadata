select 'create database metadata' where not exists (select from pg_database where datname = 'metadata')\gexec
\c metadata
