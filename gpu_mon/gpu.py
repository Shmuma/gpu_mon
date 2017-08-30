import glob
import collections

GPUInfo = collections.namedtuple('GPUInfo', field_names=['file_name', 'id'])


def detect_gpus():
    """
    Return list of GPUInfo preset in system
    """
    result = []
    prefix = "/dev/nvidia"
    for file_name in glob.glob(prefix + '*'):
        id_str = file_name[len(prefix):]
        try:
            id_int = int(id_str)
            result.append(GPUInfo(file_name=file_name, id=id_int))
        except ValueError:
            pass
    result.sort(key=lambda g: g.id)
    return result


def format_gpu_id(gpu_id):
    """
    Represent gpu id in text form
    :param gpu_id: None if all gpus or int gpu id
    :return:
    """
    if gpu_id is None:
        return "all GPUs"
    else:
        return "GPU %d" % gpu_id
