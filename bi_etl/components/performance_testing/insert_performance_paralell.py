from bi_etl.bi_config_parser import BIConfigParser

from bi_etl.database.connect import Connect

from datetime import datetime, date
import time

import bi_etl.parallel.mp as mp


def now():
    return time.perf_counter()


def timepassed(time_started, message):
    print(f"{message:55s} took {now() - time_started:3.4f}")


def insert_deamon(config, Connect, con_name, queue, proc_number, max_rows=5000):
    engine = Connect.get_sqlachemy_engine(config, con_name)
    con = engine.connect()
    cols = 'c1,c2,dt,dt2,i1,f1,d1'
    col_cnt = len(cols.split(','))
    insert_sql = f"INSERT INTO perf_test ({cols}) VALUES ({','.join(['%s'] * col_cnt)})"

    done = False
    pending_rows = []
    while not done:
        try:
            row = queue.get()
            if row == 'DONE':
                done = True
                if len(pending_rows) > 0:
                    con.execute(insert_sql, pending_rows)
                print(f"Process {proc_number} got DONE -- {len(pending_rows)} pending rows left")
                queue.put(row)
            else:
                # print(row)
                pending_rows.append(row)
                if len(pending_rows) >= max_rows:
                    print(f"Process {proc_number} flushing {len(pending_rows)} pending rows")
                    con.execute(insert_sql, pending_rows)
                    pending_rows = []
        except Exception as e:
            print(f"Process {proc_number} exception: {e}")
    con.execute("COMMIT")
    con.close()
    print(f"Process {proc_number} done")
    return 1


def test_connection(test, config, con_name, row_list, pool_size=4):
    rows = len(row_list)
    engine = Connect.get_sqlachemy_engine(config, con_name)
    con = engine.connect()
    con.execute("TRUNCATE TABLE perf_test")
    con.execute("COMMIT; VACUUM perf_test; COMMIT;")
    con.close()
    started = now()

    processes_pool = []
    row_queue = mp.Queue()

    print(f"Starting pool of {pool_size} processes")
    for proc_number in range(pool_size):
        p = mp.Process(
            target=insert_deamon,
            args=(config,
                  Connect,
                  con_name,
                  row_queue,
                  proc_number,
                  int(rows/pool_size))
        )
        p.start()
        processes_pool.append(p)

    print("Queueing rows")
    for row in row_list:
        row_queue.put(row)

    print("Queueing DONE")
    row_queue.put('DONE')

    print("Joining")
    for p in processes_pool:
        p.join()

    timepassed(started, f'{test}: {rows} to DB parallel {pool_size}')


def main():
    row_list = []
    rows = 1000
    for i in range(rows):
        dt = date(
            2017,
            (12 - i) % 12 + 1,
            i % 28 + 1,
            )
        dt2 = datetime.now()
        row_list.append([
            f'hello{i}',
            f'2this is a test #{i % 5}',
            dt,
            dt2,
            i,
            i/10,
            i/100,
            ]
        )

    print("Starting test")

    config = BIConfigParser()
    config.read_config_ini(file_name='perf_config.ini')
    test_connection(f'sqlalchemy perf_test2 config',
                    config,
                    'perf_test2',
                    row_list,
                    )


if __name__ == '__main__':
    main()
