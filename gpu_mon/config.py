import configparser


def parse_gpu_indices(indices_str):
    assert isinstance(indices_str, str)
    if indices_str.lower() == 'all':
        indices = None
    else:
        indices = set(map(int, indices_str.split(',')))
    return indices


class GPUConfiguration:
    def __init__(self, gpu_indices, ignore_programs):
        assert isinstance(gpu_indices, (set, type(None)))
        assert isinstance(ignore_programs, list)
        self.gpu_indices = gpu_indices
        self.ignore_programs = ignore_programs

    @classmethod
    def config_from_section(cls, section):
        assert isinstance(section, configparser.SectionProxy)
        indices = parse_gpu_indices(section['gpus'])
        ignore_programs = section['ignore_programs'].split(',')
        return GPUConfiguration(indices, ignore_programs)

    @classmethod
    def configs_from_parser(cls, parser):
        assert isinstance(parser, configparser.ConfigParser)
        result = []
        for sect in parser.sections():
            if sect.startswith('gpu'):
                conf = cls.config_from_section(parser[sect])
                if conf:
                    result.append(conf)
        return result


class ProcessConfiguration:
    def __init__(self, gpu_indices, dir, cmd):
        assert isinstance(gpu_indices, (set, type(None)))
        assert isinstance(dir, str)
        assert isinstance(cmd, str)
        self.gpu_indices = gpu_indices
        self.dir = dir
        self.cmd = cmd

    @classmethod
    def config_from_section(cls, section):
        assert isinstance(section, configparser.SectionProxy)
        indices = parse_gpu_indices(section['gpus'])
        dir = section['dir']
        cmd = section['cmd']
        return ProcessConfiguration(indices, dir, cmd)

    @classmethod
    def configs_from_parser(cls, parser):
        assert isinstance(parser, configparser.ConfigParser)
        result = []
        for sect in parser.sections():
            if sect.startswith('process'):
                conf = cls.config_from_section(parser[sect])
                if conf:
                    result.append(conf)
        return result


class TTYConfiguration:
    def __init__(self, enabled, whitelist, idle_seconds):
        assert isinstance(enabled, bool)
        assert isinstance(whitelist, list)
        assert isinstance(idle_seconds, int)
        self.enabled = enabled
        self.whitelist = whitelist
        self.idle_seconds = idle_seconds

    @classmethod
    def config_from_section(cls, section):
        assert isinstance(section, configparser.SectionProxy)
        enabled = section.getboolean('enabled')
        whitelist = section.get('whitelist', fallback='').split(',')
        idle_seconds = section.getint('idle_seconds', fallback=0)
        return TTYConfiguration(enabled, whitelist, idle_seconds)

class Configuration:
    def __init__(self, interval_seconds, gpus_conf, processes_conf, tty_conf):
        self.interval_seconds = interval_seconds
        self.gpus_conf = gpus_conf
        self.processes_conf = processes_conf
        self.tty_conf = tty_conf

    @classmethod
    def config_from_parser(cls, parser):
        assert isinstance(parser, configparser.ConfigParser)
        interval_seconds = parser['defaults'].getint('interval_seconds')
        gpus = GPUConfiguration.configs_from_parser(parser)
        processes = ProcessConfiguration.configs_from_parser(parser)
        tty_conf = TTYConfiguration.config_from_section(parser['tty'])
        return Configuration(interval_seconds, gpus, processes, tty_conf)

    @classmethod
    def read(cls, file_name):
        conf = configparser.ConfigParser()
        if not conf.read(file_name):
            raise FileNotFoundError("Configuration not found: %s" % file_name)
        return cls.config_from_parser(conf)
