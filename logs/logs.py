import colorama
import pytz
from datetime import datetime

time_sp = pytz.timezone("America/Sao_Paulo")
data_hora = datetime.now(time_sp).strftime("%Y-%m-%d %H:%M:%S")


class Logs():

    @staticmethod
    def _now():
        time_sp = pytz.timezone("America/Sao_Paulo")
        data_hora = datetime.now(time_sp).strftime("%Y-%m-%d %H:%M:%S") 
        return data_hora

    @staticmethod
    def log_sucess(string):
        print(colorama.Fore.LIGHTGREEN_EX,f"{Logs._now()} ======= LOG ======== > {string}",colorama.Fore.RESET)

    @staticmethod
    def log_fail(string):    
        print(colorama.Fore.LIGHTRED_EX,f"{Logs._now()} ======= LOG ======== > {string}",colorama.Fore.RESET)

    @staticmethod
    def log_warning(string):    
        print(colorama.Fore.LIGHTYELLOW_EX,f"{Logs._now()} ======= LOG ======== > {string}",colorama.Fore.RESET)


    @staticmethod
    def log_step(string):    
        print(colorama.Fore.LIGHTCYAN_EX,f"{Logs._now()} ======= LOG ======== > {string}",colorama.Fore.RESET)





