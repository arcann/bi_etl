exec utils.drop_object 'dbo', 'perf_test';

create table dbo.perf_test (
  c1 varchar(25),
  C2 varchar(100),
  dt datetime,
  dt2 datetime2,
  i1 int,
  f1 FLOAT,
  d1 decimal(38,6)
);