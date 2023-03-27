import logging
import os
import sys

def setup_log(log_dir='', log_level=logging.INFO, section_name=''):
    """
    Set up the basics of logging system. We have two logging handlers:
    one to the console and the other to a log file
    :param log_dir:
    :param log_level:
    :return:
    """
    SPLIT_STR = '\\' if 'win' in sys.platform else '/'
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    logging.basicConfig(
        format='%(asctime)s %(levelname)s '
               '%(module)s - %(funcName)s: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        handlers=[
            logging.FileHandler(log_dir + SPLIT_STR + 'running_results_{}.log'.format(section_name),
                                mode='w'),
            logging.StreamHandler()
        ],
        level=log_level
    )
    return
