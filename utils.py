import time


log_config = {
}


def set_log_path():
    fmt = '%Y%m%d%H%M%S'
    value = time.localtime(int(time.time()))
    dt = time.strftime(fmt, value)
    log_config['file'] = 'logs/log.{}.txt'.format(dt)


def log(*args, **kwargs):
    # time.time() 返回 unix time
    fmt = '%Y/%m/%d %H:%M:%S'
    value = time.localtime(int(time.time()))
    dt = time.strftime(fmt, value)
    # 这样确保了每次运行都有一个独立的 path 存放 log
    path = log_config.get('file')
    if path is None:
        set_log_path()
        path = log_config['file']
    with open(path, 'a', encoding='utf-8') as f:
        print(dt, *args, file=f, **kwargs)




