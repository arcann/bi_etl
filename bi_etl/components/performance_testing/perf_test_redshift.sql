drop table if EXISTS public.perf_test;

-- create table public.perf_test (
--   c1 varchar(25) not null ENCODE Text255,
--   C2 varchar(100) ENCODE BYTEDICT,
--   dt DATE not null ENCODE RAW,
--   dt2 TIMESTAMP not null ENCODE RAW,
--   i1 int not null ENCODE DELTA,
--   f1 FLOAT not null ENCODE RAW,
--   d1 decimal(38,6) not null ENCODE MOSTLY16,
--   PRIMARY KEY (i1)
-- )
--   distkey(i1)
--   compound sortkey(dt , i1)
-- ;

create table public.perf_test (
  i1 int not null ENCODE delta32k DISTKEY,
  c1 varchar(25) null ENCODE zstd,
  C2 varchar(100) ENCODE zstd,
  dt DATE not null ENCODE zstd,
  dt2 TIMESTAMP not null ENCODE zstd,
  f1 FLOAT not null ENCODE zstd,
  d1 decimal(38,6) not null ENCODE zstd,
  PRIMARY KEY (i1)
)
  diststyle key
  INTERLEAVED SORTKEY (i1, c1, dt)
;

-- create table public.perf_test (
--   i1 int not null ENCODE raw,
--   c1 varchar(25) null ENCODE raw,
--   C2 varchar(100) ENCODE raw,
--   dt DATE not null ENCODE raw,
--   dt2 TIMESTAMP not null ENCODE RAW,
--   f1 FLOAT not null ENCODE RAW,
--   d1 decimal(38,6) not null ENCODE raw,
--   PRIMARY KEY (i1)
-- )
--   diststyle ALL
--   compound sortkey(i1)
-- ;


-- create table public.perf_test (
--   i1 int not null ENCODE raw,
--   c1 varchar(25) not null ENCODE raw,
--   C2 varchar(100) ENCODE raw,
--   dt DATE not null ENCODE raw,
--   dt2 TIMESTAMP not null ENCODE RAW,
--   f1 FLOAT not null ENCODE RAW,
--   d1 decimal(38,6) not null ENCODE raw,
--   PRIMARY KEY (i1)
-- )
--   diststyle even
--   compound sortkey(i1, dt)
-- ;