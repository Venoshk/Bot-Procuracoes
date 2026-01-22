import base64
import os
import time

import requests
from deep_translator import GoogleTranslator
from dotenv import dotenv_values,load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utils.deleteFiles import deleteFiles
from time import sleep


from logs.logs import Logs

load_dotenv()

config = dotenv_values(".env")
api_key = os.getenv('CAPTCHA_SOLVER_API_KEY')
directoryPath = os.getenv('FOLDER_PATH')


def handleImagesSaving(driver, captchaTaskImagePaths, captchaHelperImagePath):
    wait = WebDriverWait(driver, 5)

    taskImages = wait.until(
        EC.visibility_of_all_elements_located(
            (By.XPATH, '''
        /html/body/div/div[1]/div/div/div[2]/div
        ''')
        )
    )

    for idx, taskImage in enumerate(taskImages):
        image = taskImage.find_element(
            By.XPATH, f'/html/body/div/div[1]/div/div/div[2]/div[{idx+1}]/div[2]/div/div[1]')
        styles = image.get_attribute('style')
        src = styles[styles.find("(")+1:styles.find(")")].replace('"', '')
        img_data = requests.get(src).content

        with open(os.path.join(directoryPath, f'{idx+1}_captcha_task.jpg'), 'wb') as handler:
            handler.write(img_data)
        base64Task = base64.b64encode(
            open(
                os.path.join(
                    directoryPath, f'{idx+1}_captcha_task.jpg'), 'rb'
            ).read()
        ).decode('utf-8')
        captchaTaskImagePaths.append(base64Task)

    try:
        helper_image = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, '''
                body > div > div.challenge-container > div > div > div.challenge-header > div.challenge-prompt > div.examples > div > div > div.image > div.image
            ''')
            )
        )

        styles = helper_image.get_attribute('style')

        helperSrc = styles[styles.find(
            "(")+1:styles.find(")")].replace('"', '')

        img_data = requests.get(helperSrc).content
        with open(os.path.join(directoryPath, 'captcha_helper.jpg'), 'wb') as handler:
            handler.write(img_data)

        base64Helper = base64.b64encode(
            open(os.path.join(directoryPath, 'captcha_helper.jpg'), 'rb').read()
        ).decode('utf-8')
        captchaHelperImagePath.append(base64Helper)
    except Exception:
        Logs.log_warning("-----------Sem imagem de apoio-----------")
        pass


def handleAnswering(driver, result):
    wait = WebDriverWait(driver, 150)
    answersList = []
    objects = result['objects']

    for index, booleanValue in enumerate(objects):
        if booleanValue is True:
            answersList.append(index + 1)

    Logs.log_step(f"-----------PREENCHENDO RESPOSTAS: {answersList}-----------")

    for answer in answersList:
        sleep(2)
        time.sleep(0.5)
        taskImage = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f'''
              /html/body/div/div[1]/div/div/div[2]/div[{answer}]
            ''')
            )
        )
        taskImage.click()

    advanceButton = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, '''
        /html/body/div/div[3]/div[3]
        ''')
        )
    )
    advanceButtonText = advanceButton.text

    sleep(2)
    advanceButton.click()
    return advanceButtonText


def captchaSolver(driver):
    wait = WebDriverWait(driver, 5)
    apiUrl = 'https://api.yescaptcha.com/createTask'
    captchaHelperImagePath = []
    captchaTaskImagePaths = []

    handleImagesSaving(driver, captchaTaskImagePaths, captchaHelperImagePath)

    Logs.log_warning("-----------INICIANDO RESOLUÇÃO DE HCAPTCHA-----------")

    captchaHintText = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, '''
        /html/body/div/div[1]/div/div/div[1]/div[1]/div[1]/h2/span
        ''')
        )
    ).text
    translatedCaptchaHint = GoogleTranslator(
        source='pt', target='en'
    ).translate(captchaHintText)

    data = {
        "clientKey": api_key,
        "task": {
            "type": "HCaptchaClassification",
            "queries": captchaTaskImagePaths,
            "question": translatedCaptchaHint,
        }
    }

    if len(captchaHelperImagePath) > 0:
        data['task']['anchors'] = captchaHelperImagePath

    try:
        response = requests.post(apiUrl, json=data)
        result = response.json()

        if result['errorId'] == 0:
            Logs.log_sucess("-----------RESPOSTA COLETADA-----------")

            advanceButtonText = handleAnswering(driver, result['solution'])

            if 'Verificar' in advanceButtonText:
                Logs.log_sucess("-----------CAPTCHA RESOLVIDO-----------")
                driver.switch_to_parent_frame()
                Logs.log_step("-----------RETORNANDO PARA FRAME PRINCIPAL-----------")
                deleteFiles(directoryPath)
                return
            else:
                Logs.log_step("-----------PÁGINA RESOLVIDA, AVANÇANDO-----------")
                captchaSolver(driver)
        else:
            errorCode = result['errorCode']
            raise Exception(
                'captcha', f'FALHA EM RESOLUÇÃO DE CAPTCHA: {errorCode}', 'Sem detalhes')
    except Exception as e:
        raise Exception(
            'captcha', 'FALHA EM RESOLUÇÃO DE CAPTCHA', e)


def yesCaptchaHandler(driver):
    Logs.log_step("-----------ATIVANDO HCAPTCHA-----------")

    try:
        driver.switch_to_frame('/html/body/div[3]/div[1]/iframe')
        Logs.log_step("-----------HCAPTCHA ENCONTRADO-----------")
        Logs.log_sucess("-----------MUDANÇA DE ACESSO PARA IFRAME HCAPTCHA-----------")

        captchaSolver(driver)
        sleep()
    except Exception:
        Logs.log_fail(
            "-----------HCAPTCHA NÃO ENCONTRADO, CONTINUANDO-----------")
        pass