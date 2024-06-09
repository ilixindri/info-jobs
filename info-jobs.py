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
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
import time
from math import ceil

# Configuração do módulo de logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s',
                    handlers=[
                        logging.FileHandler("infojobs.log"),  # Salva os logs em um arquivo
                        logging.StreamHandler(sys.stdout)    # Imprime os logs na tela
                    ])

class WebDriverManager:
    def __init__(self, driver_path):
        self.driver_path = driver_path
        self.driver = None

    def setup_driver(self):
        try:
            edge_service = EdgeService(self.driver_path)
            edge_options = EdgeOptions()
            edge_options.add_argument('--headless')
            edge_options.add_argument('--disable-gpu')
            edge_options.add_argument('--no-sandbox')
            edge_options.add_argument('--disable-dev-shm-usage')
            edge_options.add_argument('--remote-debugging-port=9222')
            edge_options.binary_location = "/usr/bin/microsoft-edge-dev"
            
            # Criando uma instância do driver do navegador Edge com o serviço especificado
            self.driver = webdriver.Edge(service=edge_service, options=edge_options)
            logging.info("Driver configurado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao configurar o driver: {e}")
            raise

    def quit_driver(self):
        if self.driver:
            self.driver.quit()
            logging.info("Driver finalizado.")

class InfoJobsLogin:
    def __init__(self, email, password, driver_manager):
        self.email = email
        self.password = password
        self.driver_manager = driver_manager

    def login(self):
        try:
            logging.info("Iniciando login.")
            self.driver_manager.driver.get("https://login.infojobs.com.br/Account/Login")
            #WebDriverWait(self.driver_manager.driver, 10).until(EC.presence_of_element_located((By.ID, "Email")))

            logging.info("Cookies")
            # Clicando no botão "Saiba mais"
            saiba_mais_button = WebDriverWait(self.driver_manager.driver, 10).until(EC.element_to_be_clickable((By.ID, "didomi-notice-learn-more-button")))
            saiba_mais_button.click()
            
            # Clicando no botão "Não aceito nenhum"
            nao_aceito_button = WebDriverWait(self.driver_manager.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.didomi-button-standard")))
            nao_aceito_button.click()
            
            logging.info("Inserindo e-mail.")
            email_input = WebDriverWait(self.driver_manager.driver, 10).until(EC.presence_of_element_located((By.ID, "Email")))
            email_input.send_keys(self.email)
            email_input.send_keys(Keys.ENTER)
            
            logging.info("Inserindo senha.")
            password_input = WebDriverWait(self.driver_manager.driver, 10).until(EC.presence_of_element_located((By.ID, "Password")))
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.ENTER)
            
            WebDriverWait(self.driver_manager.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.logged-in-element")))
            logging.info("Login realizado com sucesso.")
        except Exception as e:
            logging.error(f"Erro durante o login: {e}")
            raise

class InfoJobsScraper:
    def __init__(self, driver_manager):
        self.driver_manager = driver_manager

    def click_all_cards(self):
        try:
            logging.info("Iniciando click em todos os cards.")
            # Navegar até a página inicial
            self.driver_manager.driver.get("https://www.infojobs.com.br/empregos-em-sao-paulo.aspx")
            
            # Obter o número total de páginas
            total_pages = self.get_total_pages()
            
            # Iterar sobre todas as páginas
            for page_number in range(1, total_pages + 1):
                logging.info(f"Navegando para a página {page_number}")
                
                # Navegar para a página específica
                self.navigate_to_page(page_number)
                
                # Clique em todos os cards na página atual
                self.click_all_cards_on_page()
                
            logging.info("Click em todos os cards concluído.")
        except Exception as e:
            logging.error(f"Erro durante o click em todos os cards: {e}")
            raise

    def get_total_pages(self):
        jobs_element = WebDriverWait(self.driver_manager.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.small.text-medium")))
        total_jobs_text = jobs_element.text.strip().split()[0]
        total_jobs = float(total_jobs_text)
        cards_per_page = len(WebDriverWait(self.driver_manager.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card.card-shadow.card-shadow-hover.text-break.mb-16.grid-row.js_rowCard.active"))))
        total_pages = ceil(total_jobs / cards_per_page)
        return total_pages

    def navigate_to_page(self, page_number):
        url = f"https://www.infojobs.com.br/empregos-em-sao-paulo.aspx?page={page_number}&campo=griddate&orden=desc"
        self.driver_manager.driver.get(url)
        WebDriverWait(self.driver_manager.driver, 10).until(EC.presence_of_element_located((By.ID, "filterSideBar")))

    def click_all_cards_on_page(self):
        logging.info("Iniciando click em todos os cards da página.")
        try:
            card_divs = WebDriverWait(self.driver_manager.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card.card-shadow.card-shadow-hover.text-break.mb-16.grid-row.js_rowCard")))
        except NoSuchElementException:
            logging.error("Nenhum card encontrado.")
            return

        for index, card_div in enumerate(card_divs, start=1):
            try:
                modal = self.driver_manager.driver.find_element(By.CSS_SELECTOR, "div.modal-content")
                if modal:
                    discard_button = modal.find_element(By.ID, "btnSharedLooseChangesModalDiscardForm")
                    discard_button.click()
                    time.sleep(2)
            except NoSuchElementException:
                pass

            card_link = card_div.find_element(By.CSS_SELECTOR, "a.text-decoration-none")
            card_name = card_link.find_element(By.CSS_SELECTOR, "h2").text.strip()
            logging.info(f"Clicando no card {index} '{card_name}' de {len(card_divs)}")
            card_div.click()
            time.sleep(2)

            try:
                apply_button = WebDriverWait(self.driver_manager.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary.btn-block.js_buttonloading.js_btApplyVacancy")))
                apply_button.click()
                logging.info("Botão de aplicar clicado com sucesso.")
                time.sleep(2)
            except NoSuchElementException:
                logging.error("Botão de aplicar não encontrado.")
            except ElementClickInterceptedException:
                logging.error("Não foi possível clicar no botão de aplicar. Isso pode ocorrer quando outro elemento intercepta o clique, como um modal ou um overlay.")
            except ElementNotInteractableException:
                logging.error("Não foi possível clicar no botão de aplicar. Isso pode ocorrer se o botão estiver oculto, desabilitado ou fora da área visível da página.")

            self.driver_manager.driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script de login no InfoJobs")
    parser.add_argument("-d", "--driver_path", required=True, help="Caminho para o executável do WebDriver")
    parser.add_argument("-e", "--email", required=True, help="Endereço de e-mail para login")
    parser.add_argument("-p", "--password", required=True, help="Senha para login")
    args = parser.parse_args()

    driver_manager = WebDriverManager(args.driver_path)
    driver_manager.setup_driver()

    login_instance = InfoJobsLogin(args.email, args.password, driver_manager)
    login_instance.login()

    scraper_instance = InfoJobsScraper(driver_manager)
    scraper_instance.click_all_cards()

    driver_manager.quit_driver()
