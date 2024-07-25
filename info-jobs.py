
"""Aplicar-se a todas as vagas do InfoJobs

Na primeira vez que o código for executado
salvar o primeiro card_iv no arquivo first
e não salvar mais nada no arquivo first.

Ao aplicar-se a uma vaga acrescentar o card_iv
dessa vaga ao arquivo applied e sobreescrever
no arquivo actual.

Quando o código for executado nas próximas vezes
aplicar-se a todas as vagas iniciais até o card_iv
do arquivo fisrt. E não aplicar-se às vagas entre 
first e actual e aplicar-se nas vagas após a actual.

Todos os cards que não receberão apply devem ser
guardados os iv no arquivo 'puladas'.
"""
import argparse
import logging
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, TimeoutException, UnexpectedAlertPresentException
from math import ceil
from urllib.parse import urlparse, parse_qs
import os
import time

# Configuração do módulo de logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s',
                    handlers=[
                        logging.FileHandler("infojobs.log"),
                        logging.StreamHandler(sys.stdout)
                    ])

class WebDriverManager:
    def __init__(self, driver_path):
        self.driver_path = driver_path
        self.driver = None

    def setup_driver(self, binary_location=None):
        try:
            edge_service = EdgeService(self.driver_path)
            edge_options = EdgeOptions()
            edge_options.use_chromium = True
            edge_options.add_argument('--disable-gpu')
            edge_options.add_argument('--no-sandbox')
            edge_options.add_argument('--disable-dev-shm-usage')
            edge_options.add_argument('--remote-debugging-port=9222')

            if binary_location:
                edge_options.binary_location = binary_location

            self.driver = webdriver.Edge(service=edge_service, options=edge_options)
            # self.driver.maximize_window()
            self.driver.set_window_size(1366, 600)
            self.driver.set_window_position(0, 0)
            logging.info("Driver configurado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao configurar o driver: {e}")
            raise

    def quit_driver(self):
        if self.driver:
            self.driver.quit()
            logging.info("Driver finalizado.")

class InfoJobs:
    def __init__(self, driver_manager):
        self.driver_manager = driver_manager

    def accept_cookies(self):
        try:
            logging.info("Aceitando cookies...")
            self.driver_manager.driver.get('https://www.infojobs.com.br/')
            self.click_button(By.ID, "didomi-notice-learn-more-button", "Saiba mais")
            time.sleep(10)
            self.click_button(By.CSS_SELECTOR, "button.didomi-button-standard", "Não aceito nenhum")
        except Exception as e:
            logging.error(f"Erro ao configurar cookies: {e}")
            raise

    def click_button(self, by, selector, button_description):
        try:
            button = WebDriverWait(self.driver_manager.driver, 10).until(
                EC.element_to_be_clickable((by, selector))
            )
            button.click()
        except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
            logging.error(f"Erro ao clicar no botão '{button_description}': {e}")
            raise

class InfoJobsLogin:
    def __init__(self, email, password, driver_manager):
        self.email = email
        self.password = password
        self.driver_manager = driver_manager

    def login(self):
        try:
            logging.info("Realizando login...")
            self.driver_manager.driver.get("https://login.infojobs.com.br/Account/Login")
            self.enter_text(By.ID, "Email", self.email)
            self.enter_text(By.ID, "Password", self.password)
            logging.info("Login realizado com sucesso.")
        except TimeoutException:
            logging.error("Tempo limite excedido durante o login.")
            raise
        except Exception as e:
            logging.error(f"Erro durante o login: {e}")
            raise

    def enter_text(self, by, selector, text):
        input_field = WebDriverWait(self.driver_manager.driver, 20).until(
            EC.element_to_be_clickable((by, selector))
        )
        input_field.send_keys(text)
        input_field.send_keys(Keys.ENTER)

class InfoJobsScraper:
    def __init__(self, driver_manager, page_link):
        self.driver_manager = driver_manager
        self.card_iv = None
        self.page_number = None
        self.page_link = page_link

    def click_all_cards(self):
        logging.info("Clicando em todos os cards...")
        actual_iv = self.read_file('actual')
        first_iv = self.read_file('first')

        total_pages = self.get_total_pages()
        to_apply = None

        for page_number in range(1, total_pages + 1):
            self.page_number = page_number
            self.navigate_to_page(page_number)
            card_divs = self.get_all_cards_on_page()

            for index, card_div in enumerate(card_divs, start=1):
                self.handle_card(card_div, index, len(card_divs), actual_iv, first_iv, to_apply)

    def get_total_pages(self):
        self.navigate_to_page(1)
        total_jobs_text = self.get_element_text(By.CSS_SELECTOR, "span.small.text-medium").split()[0]
        total_jobs = float(total_jobs_text.replace('.', ''))
        return ceil(total_jobs / 20)

    def navigate_to_page(self, page_number):
        logging.info(f'Abrindo a página {page_number}')
        print('\n')
        with open('infojobs.log', 'a') as f:
            f.write('\n')
        url = f"{self.page_link}&page={page_number}"
        self.driver_manager.driver.get(url)

        try:
            WebDriverWait(self.driver_manager.driver, 10).until(
                EC.presence_of_element_located((By.ID, "filterSideBar"))
            )
        except UnexpectedAlertPresentException:
            WebDriverWait(self.driver_manager.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.btn-text"))
            )

    def get_all_cards_on_page(self):
        return WebDriverWait(self.driver_manager.driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "card.card-shadow.card-shadow-hover.text-break.mb-16.grid-row.js_rowCard"))
        )

    def pular_modal_break_card_div_click(self, card_div, index):
        try:
            card_link = WebDriverWait(card_div, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.text-decoration-none"))
            )
            logging.info(f'Card {index} reclicando para fechar as perguntas.')
            # logging.info('Fazendo scroll para clicar no card para abrir a seção de aplicar-se.')
            # self.scroll_to_element(card_link)
            card_link.click()
            logging.info(f'Card {index} reclicado com sucesso.')
        except TimeoutException:
            logging.error(f"Erro de tempo ao processar o card {index}.")
            raise
        except NoSuchElementException:
            logging.error(f"Elemento não encontrado ao processar o card {index}.")
            raise
        except ElementClickInterceptedException:
            logging.error(f"Erro ao clicar no card {index}. Outro elemento interceptou o clique.")
            raise
        except ElementNotInteractableException:
            logging.error(f"Erro ao interagir com o card {index}. Elemento não interagível.")
            raise
        except ElementClickInterceptedException:
            logging.error('error 00')
            raise
        except Exception as e:
            logging.error(f"Erro inesperado ao processar o card {index}: {e}")
            logging.error(f"Erro ao processar o card {index}: {e}")
            raise

        while self.element_exists(By.ID, "btnSharedLooseChangesModalDiscardForm") != False:
            if self.element_exists(By.ID, "btnSharedLooseChangesModalDiscardForm"):
                """Botão para fechar modal.

                ID = btnSharedLooseChangesModalDiscardForm
                CSS_SELECTOR = span.btn-text
                """
                try:
                    """Elemento abandonar para fechar o modal.

                    O modal é o de questionar se o user quer cancelar
                    a candidatura agora pois essas candidaturas
                    tem perguntas a preencher.
                    """
                    confirm = WebDriverWait(self.driver_manager.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "btnSharedLooseChangesModalDiscardForm"))
                    )
                except TimeoutException:
                    logging.error(f"Erro de tempo ao retornar o elemento para fechar o modal.")
                    raise
                try:
                    # logging.info('Fazendo scroll para clicar no botão do modal.')
                    # self.scroll_to_element(confirm)
                    time.sleep(10)
                    confirm.click()
                    logging.info('Botão do modal clicado. Modal fechado com sucesso.')
                except ElementClickInterceptedException:
                    logging.error('ElementClickInterceptedException')
                except ElementNotInteractableException:
                    logging.error('ElementNotInteractableException')
                except:
                    logging.error(f"Erro ao clicar para fechar o Modal.")
                    raise

    def handle_card(self, card_div, index, total_cards, actual_iv, first_iv, to_apply):
        try:
            card_link = WebDriverWait(card_div, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.text-decoration-none"))
            )
            card_name = self.get_element_text_from(card_link, By.CSS_SELECTOR, "h2").strip()

            print('\n')
            with open('infojobs.log', 'a') as f:
                f.write('\n')
            # logging.info('Fazendo scroll para clicar no card para abrir a seção de aplicar-se.')
            # self.scroll_to_element(card_link)
            card_link.click()
            time.sleep(10) #esperando o modal fechar e carregar a página do novo iv
            try:
                """Esperando a url ser alterada para pegar o id (iv) da vaga
                """
                WebDriverWait(self.driver_manager.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary.btn-block.js_buttonloading.js_btApplyVacancy"))
                )
            except:
                try:
                    """
                    """
                    # Qual é esse elemento?
                    WebDriverWait(self.driver_manager.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.h3.mb-32"))
                    )
                except:
                    pass
            self.card_iv = parse_qs(urlparse(self.driver_manager.driver.current_url).query).get('iv')[0]

            if not first_iv:
                # self.write_file('first', card_iv)
                first_iv = self.card_iv

            to_apply = first_iv is None or actual_iv != first_iv or actual_iv is None
            if actual_iv == self.card_iv:
                to_apply = True

            if to_apply:
                logging.info(f"Clicando no card {index}/{total_cards} com nome '{card_name}', 'iv' {self.card_iv} e page {self.page_number}.")
                self.apply_for_job(card_div, index)
                # self.write_file('actual', card_iv)

            if first_iv == self.card_iv:
                to_apply = False
            if actual_iv == self.card_iv:
                to_apply = True
        except TimeoutException:
            logging.error(f"Erro de tempo ao processar o card {index}.")
            raise
        except NoSuchElementException:
            logging.error(f"Elemento não encontrado ao processar o card {index}.")
            raise
        except ElementClickInterceptedException:
            logging.error(f"Erro ao clicar no card {index}. Outro elemento interceptou o clique.")
            raise
        except ElementNotInteractableException:
            logging.error(f"Erro ao interagir com o card {index}. Elemento não interagível.")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado ao processar o card {index}: {e}")
            logging.error(f"Erro ao processar o card {index}: {e}")
            raise

    def apply_for_job(self, card_div, index):
        try:
            apply_button = WebDriverWait(self.driver_manager.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary.btn-block.js_buttonloading.js_btApplyVacancy"))
            )
            logging.info('Botão de aplicar-se pronto para ser clicado.')
            apply_button.click()
            logging.info('Botão de aplicar-se clicado.')
        except TimeoutException:
            logging.error("Tempo limite excedido ao tentar aplicar-se à vaga.")
            logging.error("Pode ser vaga com perguntas a responder.")
        except ElementClickInterceptedException:
            logging.error("Outro elemento interceptou o clique no botão de aplicar.")
            raise
        except ElementNotInteractableException:
            logging.error("O botão de aplicar não está interagível (oculto ou desabilitado).")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado ao tentar aplicar-se à vaga: {e}")
            raise

        if self.element_exists(By.CSS_SELECTOR, 'div.h3.mb-32'):
            """Elemento no início dos campos para preencher.

            Text: 'Para concluir a candidatura responda as seguintes perguntas:'.
            Precisa preencher os campos. Utilisar OpenAi.
            """
            logging.info("Vaga requer respostas a perguntas adicionais.")
            logging.info('Pulando vaga.')
            self.pular_modal_break_card_div_click(card_div, index)

        # Registrando a aplicação no arquivo 'applied'
        if self.card_iv:
            with open('applied', 'a') as f:
                f.write(self.card_iv + '\n')
        if int(self.read_file('first_exists')):
            self.write_file('first', self.card_iv)
            self.write_file('first_exists', '1')

    def get_element_text(self, by, selector):
        element = WebDriverWait(self.driver_manager.driver, 10).until(
            EC.presence_of_element_located((by, selector))
        )
        return element.text

    def get_element_text_from(self, parent, by, selector):
        try:
            element = WebDriverWait(parent, 10).until(
                EC.presence_of_element_located((by, selector))
            )
            return element.text
        except TimeoutException:
            raise

    def read_file(self, filename):
        try:
            with open(filename, 'r') as file:
                return file.readline().strip()
        except FileNotFoundError:
            logging.warning(f"Arquivo '{filename}' não encontrado.")
            return None

    def write_file(self, filename, content):
        try:
            with open(filename, 'w') as file:
                file.write(content)
        except Exception as e:
            logging.error(f"Erro ao escrever no arquivo '{filename}': {e}")
            raise

    def scroll_to_element(self, element):
        self.driver_manager.driver.execute_script("arguments[0].scrollIntoView();", element)

    def element_exists(self, by, value):
        logging.info(f'Verificando se o elemento {value} exite.')
        try:
            WebDriverWait(self.driver_manager.driver, 10).until(
                EC.presence_of_element_located((by, value))
            )
            logging.info(f'O elemento {value} exite.')
            return True
        except TimeoutException:
            logging.info(f'O elemento {value} não exite.')
            return False
        except NoSuchElementException:
            logging.info(f'O elemento {value} não exite.')
            return False

def files_create():
    dir_name = os.path.dirname(__file__)
    file_names = ['actual', 'first', 'applied', 'first_exists', 'puladas']
    for file_name in file_names:
        file_path = os.path.join(dir_name, f'{file_name}.txt')
        with open(file_path, 'w') as file:
            file.write(f'0')
    print("Arquivos criados com sucesso!")


def main(driver_path, binary_location, email, password, page_link):
    files_create()
    driver_manager = WebDriverManager(driver_path)
    try:
        driver_manager.setup_driver(binary_location)

        infojobs = InfoJobs(driver_manager)
        infojobs.accept_cookies()

        login = InfoJobsLogin(email, password, driver_manager)
        login.login()

        scraper = InfoJobsScraper(driver_manager, page_link)
        scraper.click_all_cards()
    finally:
        driver_manager.quit_driver()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automatizar aplicação de vagas no InfoJobs')
    parser.add_argument('--driver-path', required=True, help='Caminho para o driver do Edge')
    parser.add_argument('--binary-location', required=False, help='Caminho para o executável do Edge')
    parser.add_argument('--email', required=True, help='Email para login no InfoJobs')
    parser.add_argument('--password', required=True, help='Senha para login no InfoJobs')
    parser.add_argument('--page_link', required=True, help='Link da página de pesquisa com os cartões a enviar candidatura.')
    args = parser.parse_args()
    main(args.driver_path, args.binary_location, args.email, args.password, args.page_link)
