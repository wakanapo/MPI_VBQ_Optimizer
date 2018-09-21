import sys
import subprocess
from fcntl import fcntl, F_SETFL, F_GETFL
from os import O_NONBLOCK

def non_blocking_read(output):
    fd = output.fileno()
    fl = fcntl(fd, F_GETFL)
    fcntl(fd, F_SETFL, fl | O_NONBLOCK)
    try:
        return output.read()
    except:
        return ""

def run(genom_name, model_name, quantize_layer):
    server = subprocess.Popen('python src/services/genom_evaluation_server.py {} {}'.format(model_name, quantize_layer),
                            shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        s_line = non_blocking_read(server.stdout)
        if s_line:
            sys.stdout.write(s_line.decode('utf-8'))
            if 'Server Ready' in s_line.decode('utf-8'):
                break
        if not s_line and server.poll() is not None:
            print('Server Error.')
            return
        
    for _ in range(1):
        client = subprocess.Popen('./bin/client {} {} {}'.format(genom_name, model_name, quantize_layer), shell=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            s_line = non_blocking_read(server.stdout)
            c_line = non_blocking_read(client.stdout)
            if s_line:
                sys.stdout.write(s_line.decode('utf-8'))
            elif server.poll() is not None:
                print('Server Error.')
                return
            if c_line:
                sys.stdout.write(c_line.decode('utf-8'))
            elif client.poll() is not None:
                break

    server.kill()

        
if __name__=='__main__':
    argv = sys.argv
    if len(argv) != 4:
        print('Usage: python ga_executor.py <genom name> <model name> <quantize_layer>')
        exit()
    run(argv[1], argv[2], argv[3])

