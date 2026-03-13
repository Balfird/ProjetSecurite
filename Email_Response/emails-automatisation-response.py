#!/usr/bin/env python3
"""
Script d'automatisation d'emails avec configuration JSON
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import logging
import time
import json
import os
from typing import List, Dict, Optional
import sys
import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import urlparse

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Configuration pour un compte email"""
    email_address: str
    password: str
    imap_server: str
    imap_port: int
    smtp_server: str
    smtp_port: int
    is_gmail: bool = False


@dataclass
class EmailMessage:
    """Représentation d'un email"""
    id: str
    sender: str
    subject: str
    content: str
    date: str


class ConfigLoader:
    """Charge la configuration depuis un fichier JSON"""

    @staticmethod
    def load_prompts(prompts_path: str = 'prompts.json') -> Dict:
        """
        Charge les prompts depuis un fichier JSON
        
        Args:
            prompts_path: Chemin vers le fichier de prompts
        
        Returns:
            Prompts sous forme de dictionnaire
        """
        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            logger.info(f"Prompts chargés depuis {prompts_path}")
            return prompts
        except FileNotFoundError:
            logger.error(f"Fichier de prompts non trouvé : {prompts_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON des prompts : {e}")
            raise
    
    @staticmethod
    def load_config(config_path: str = 'config.json') -> Dict:
        """
        Charge la configuration depuis un fichier JSON
        
        Args:
            config_path: Chemin vers le fichier de configuration
        
        Returns:
            Configuration sous forme de dictionnaire
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Configuration chargée depuis {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Fichier de configuration non trouvé : {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON : {e}")
            raise
    
    @staticmethod
    def create_email_configs(config: Dict) -> List[EmailConfig]:
        """
        Crée les objets EmailConfig depuis la configuration
        
        Args:
            config: Dictionnaire de configuration
        
        Returns:
            Liste d'EmailConfig
        """
        configs = []
        
        for account in config.get('accounts', []):
            email_config = EmailConfig(
                email_address=account['email_address'],
                password=account['password'],
                imap_server=account['imap_server'],
                imap_port=account['imap_port'],
                smtp_server=account['smtp_server'],
                smtp_port=account['smtp_port'],
                is_gmail=account.get('is_gmail', False)
            )
            configs.append(email_config)
        
        logger.info(f"{len(configs)} compte(s) email configuré(s)")
        return configs


class OllamaClient:
    """Client pour interagir avec Ollama pour la génération de réponses"""
    
    def __init__(self, base_url: str = 'http://localhost:11434', model: str = 'mistral', prompts: Dict = None):
        self.base_url = base_url
        self.model = model
        self.prompts = prompts or {}
        self._check_ollama_connection()
    
    def _check_ollama_connection(self):
        """Vérifie que Ollama est accessible"""
        try:
            response = requests.get(f'{self.base_url}/api/tags', timeout=5)
            response.raise_for_status()
            logger.info(f"Connexion à Ollama réussie ({self.base_url})")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Impossible de se connecter à Ollama : {e}")
            logger.warning("Le script utilisera des réponses par défaut")
    
    def generate_reply(self, email_content: str, sender: str, subject: str) -> str:
        """
        Génère une réponse professionnelle à un email
        
        Args:
            email_content: Contenu de l'email
            sender: Expéditeur de l'email
            subject: Sujet de l'email
        
        Returns:
            Réponse générée par Ollama
        """
        # Récupérer le template de prompt depuis le fichier
        prompt_template = self.prompts.get('email_reply_prompt', '')
        
        # Formater le prompt avec les variables
        prompt = prompt_template.format(
            sender=sender,
            subject=subject,
            email_content=email_content
        )

        try:
            response = requests.post(
                f'{self.base_url}/api/generate',
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                },
                timeout=90
            )
            response.raise_for_status()
            reply_text = response.json()['response']
            logger.info(f"Réponse générée avec succès ({len(reply_text)} caractères)")
            return reply_text
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la génération de réponse : {e}")
            # Réponse par défaut en cas d'erreur
            return self._get_default_reply(sender, subject)
    
    def generate_url_request(self, email_content: str, sender: str, subject: str) -> str:
        """
        Génère une réponse demandant le lien URL manquant via Ollama
        
        Args:
            email_content: Contenu de l'email reçu
            sender: Expéditeur de l'email
            subject: Sujet de l'email
        
        Returns:
            Réponse générée par Ollama demandant le lien
        """
        prompt_template = self.prompts.get('url_request_prompt', '')
        
        if not prompt_template:
            logger.warning("Prompt 'url_request_prompt' introuvable, utilisation du template par défaut")
            return self._get_url_request_fallback(subject)
        
        prompt = prompt_template.format(
            sender=sender,
            subject=subject,
            email_content=email_content
        )

        try:
            response = requests.post(
                f'{self.base_url}/api/generate',
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                },
                timeout=90
            )
            response.raise_for_status()
            reply_text = response.json()['response']
            logger.info(f"Demande de lien générée avec succès ({len(reply_text)} caractères)")
            return reply_text
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la génération de la demande de lien : {e}")
            return self._get_url_request_fallback(subject)

    def _get_url_request_fallback(self, subject: str) -> str:
        """Retourne un message de demande de lien par défaut (fallback sans Ollama)"""
        template = self.prompts.get(
            'url_request_template',
            'Bonjour,\n\nMerci pour votre message concernant "{subject}".\n\n'
            'Votre email ne contient pas de lien URL. Pourriez-vous nous le transmettre ?\n\nCordialement'
        )
        return template.format(subject=subject)

    def _get_default_reply(self, sender: str, subject: str) -> str:
        """Génère une réponse par défaut en cas d'erreur"""
        # Récupérer le template depuis le fichier
        template = self.prompts.get('default_reply_template', 
                                    'Bonjour,\n\nMerci pour votre message.\n\nCordialement')
        
        return template.format(subject=subject)

class EmailHandler:
    """Gestionnaire d'emails pour IMAP/SMTP"""
    
    def __init__(self, config: EmailConfig, ollama_client: OllamaClient):
        self.config = config
        self.ollama_client = ollama_client
        self.imap_connection = None
        self.smtp_connection = None

    def _extract_urls(self, content: str) -> List[str]:
        """
        Extrait les URLs d'un contenu email
        
        Args:
            content: Contenu de l'email
        
        Returns:
            Liste des URLs trouvées
        """
        # Regex pour détecter les URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, content)
        
        if urls:
            logger.info(f"{len(urls)} URL(s) détectée(s)")
            for url in urls:
                logger.info(f"----{url}")
        
        return urls
    
    def connect_imap(self) -> bool:
        """Connexion au serveur IMAP"""
        try:
            logger.info(f"Connexion IMAP à {self.config.imap_server}:{self.config.imap_port}")
            self.imap_connection = imaplib.IMAP4_SSL(
                self.config.imap_server,
                self.config.imap_port
            )
            self.imap_connection.login(self.config.email_address, self.config.password)
            logger.info(f" Connexion IMAP réussie pour {self.config.email_address}")
            return True
        except Exception as e:
            logger.error(f" Erreur de connexion IMAP pour {self.config.email_address}: {e}")
            return False
    
    def connect_smtp(self) -> bool:
        """Connexion au serveur SMTP"""
        try:
            logger.info(f"Connexion SMTP à {self.config.smtp_server}:{self.config.smtp_port}")
            self.smtp_connection = smtplib.SMTP(
                self.config.smtp_server,
                self.config.smtp_port
            )
            self.smtp_connection.ehlo()
            self.smtp_connection.starttls()
            self.smtp_connection.ehlo()
            self.smtp_connection.login(self.config.email_address, self.config.password)
            logger.info(f" Connexion SMTP authentifiée pour {self.config.email_address}")
            return True
        except Exception as e:
            logger.error(f" Erreur de connexion SMTP pour {self.config.email_address}: {e}")
            return False
    
    def disconnect(self):
        """Déconnexion des serveurs"""
        if self.imap_connection:
            try:
                self.imap_connection.close()
                self.imap_connection.logout()
                logger.info("Déconnexion IMAP")
            except:
                pass
        
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
                logger.info("Déconnexion SMTP")
            except:
                pass
    
    def get_unread_emails(self, max_emails: int = 50) -> List[EmailMessage]:
        """
        Récupère les emails non lus
        
        Args:
            max_emails: Nombre maximum d'emails à récupérer
        
        Returns:
            Liste des emails non lus
        """
        emails = []
        
        try:
            # Sélectionner la boîte de réception
            self.imap_connection.select('inbox')
            
            # Rechercher les emails non lus
            status, data = self.imap_connection.search(None, 'UNSEEN')
            
            if status != 'OK':
                logger.info("Aucun email non lu trouvé")
                return emails
            
            mail_ids = data[0].split()
            
            # Limiter le nombre d'emails
            if len(mail_ids) > max_emails:
                logger.warning(f"Limitation à {max_emails} emails sur {len(mail_ids)} non lus")
                mail_ids = mail_ids[:max_emails]
            
            logger.info(f" {len(mail_ids)} email(s) non lu(s) trouvé(s)")
            
            for mail_id in mail_ids:
                try:
                    email_msg = self._fetch_email(mail_id)
                    if email_msg:
                        emails.append(email_msg)
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération de l'email {mail_id}: {e}")
            
            return emails
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des emails : {e}")
            return emails
    
    def _fetch_email(self, mail_id: bytes) -> Optional[EmailMessage]:
        """Récupère un email spécifique"""
        try:
            res, msg_data = self.imap_connection.fetch(mail_id, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject = self._decode_header(msg['subject'])
                    sender = self._decode_header(msg['from'])
                    date = msg['date']
                    content = self._extract_body(msg)
                    
                    logger.info(f"  ├─ De: {sender}")
                    logger.info(f"  └─ Sujet: {subject}")
                    
                    return EmailMessage(
                        id=mail_id.decode(),
                        sender=sender,
                        subject=subject,
                        content=content,
                        date=date
                    )
            
            return None
        
        except Exception as e:
            logger.error(f"Erreur lors du fetch de l'email : {e}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """Décode un header d'email"""
        if header is None:
            return ""
        
        decoded_parts = email.header.decode_header(header)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += part
        
        return decoded_string
    
    def _extract_body(self, msg) -> str:
        """Extrait le corps de l'email"""
        content = ""
        
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            content += payload.decode(charset, errors='ignore')
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    content = payload.decode(charset, errors='ignore')
            
            return content.strip()
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du contenu : {e}")
            return ""
    
    def _archive_sent_email(self, original_email: EmailMessage, reply_content: str):
        """Archive l'email envoyé dans un dossier local pour garder une trace"""
        try:
            archive_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sent_emails')
            os.makedirs(archive_dir, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            # Extraire juste l'email si le format est "Nom <email>"
            sender_email = original_email.sender
            match = re.search(r'<([^>]+)>', sender_email)
            if match:
                sender_email = match.group(1)
            
            safe_sender = re.sub(r'[^a-zA-Z0-9_\-.]', '_', sender_email)
            filename = f"{timestamp}_{self.config.email_address}_to_{safe_sender}.txt"
            filepath = os.path.join(archive_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Date d'envoi: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Compte expediteur (IA): {self.config.email_address}\n")
                f.write(f"Destinataire: {original_email.sender}\n")
                f.write(f"Sujet: Re: {original_email.subject}\n")
                f.write("=" * 70 + "\n")
                f.write("CONTENU DE LA REPONSE ENVOYEE PAR L'IA:\n")
                f.write("-" * 70 + "\n")
                f.write(reply_content + "\n")
                f.write("=" * 70 + "\n")
                f.write("RAPPEL DE L'EMAIL ORIGINAL RECUPERE:\n")
                f.write("-" * 70 + "\n")
                f.write(f"De: {original_email.sender}\n")
                f.write(f"Date: {original_email.date}\n")
                f.write(f"Sujet: {original_email.subject}\n\n")
                f.write(original_email.content + "\n")
                f.write("=" * 70 + "\n")
                
            logger.info(f" Email envoyé archivé localement dans sent_emails/{filename}")
        except Exception as e:
            logger.error(f" Erreur lors de l'archivage de l'email : {e}")

    def send_reply(self, original_email: EmailMessage, reply_content: str) -> bool:
        """Envoie une réponse à un email, avec reconnexion SMTP automatique si timeout"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.email_address
            msg['To'] = original_email.sender
            msg['Subject'] = f"Re: {original_email.subject}"
            msg.attach(MIMEText(reply_content, 'plain', 'utf-8'))
            
            # Vérifier si la connexion SMTP est encore vivante (NOOP)
            try:
                status = self.smtp_connection.noop()
                if status[0] != 250:
                    raise Exception("Connexion SMTP morte")
            except Exception:
                # Connexion expirée : on se reconnecte
                logger.info(" Reconnexion SMTP (connexion expirée pendant la génération)...")
                if not self.connect_smtp():
                    logger.error(" Impossible de se reconnecter au SMTP")
                    return False

            self.smtp_connection.send_message(msg)
            
            # Archiver l'email envoyé localement
            self._archive_sent_email(original_email, reply_content)
            
            logger.info(f" Réponse envoyée à {original_email.sender}")
            return True
        
        except Exception as e:
            logger.error(f" Erreur lors de l'envoi de la réponse : {e}")
            return False
    
    def process_email(self, email_msg: EmailMessage) -> bool:
        """
        Traite un email :
        - Si le mail contient au moins une URL  → ignoré (aucune réponse)
        - Si le mail ne contient AUCUNE URL     → demande de lien via Ollama (gemma3)
        """
        try:
            logger.info(f" Traitement de l'email de {email_msg.sender}")
            
            # Vérifier la présence d'URLs dans l'email
            urls = self._extract_urls(email_msg.content)
            
            if urls:
                logger.info(f" URL(s) détectée(s) → email ignoré (aucune réponse envoyée)")
                return True  # On considère ça comme un succès, on ignore juste
            
            # Aucune URL : on demande le lien à l'expéditeur via Ollama
            logger.info(" Aucune URL dans l'email → génération de la demande de lien via Ollama")
            reply = self.ollama_client.generate_url_request(
                email_msg.content,
                email_msg.sender,
                email_msg.subject
            )
            
            success = self.send_reply(email_msg, reply)
            
            if success:
                logger.info(f" Demande de lien envoyée avec succès à {email_msg.sender}")
            
            return success
        
        except Exception as e:
            logger.error(f" Erreur lors du traitement de l'email : {e}")
            return False


class EmailAutomation:
    """Classe principale pour l'automatisation des emails"""
    
    def __init__(self, configs: List[EmailConfig], ollama_client: OllamaClient, max_emails_per_run: int = 50):
        self.configs = configs
        self.ollama_client = ollama_client
        self.handlers = []
        self.max_emails_per_run = max_emails_per_run
        self.stats = {
            'total_processed': 0,
            'total_sent': 0,
            'total_errors': 0
        }
    
    def setup(self) -> bool:
        """Initialise les connexions pour tous les comptes"""
        logger.info(" Initialisation des connexions...")
        
        for config in self.configs:
            handler = EmailHandler(config, self.ollama_client)
            
            if handler.connect_imap() and handler.connect_smtp():
                self.handlers.append(handler)
            else:
                logger.error(f" Échec de configuration pour {config.email_address}")
        
        if len(self.handlers) > 0:
            logger.info(f" {len(self.handlers)} compte(s) configuré(s) avec succès")
            return True
        else:
            logger.error(" Aucun compte n'a pu être configuré")
            return False
    
    def process_all_emails(self):
        """Traite les emails de tous les comptes"""
        logger.info("=" * 70)
        logger.info(" Début du traitement des emails")
        logger.info("=" * 70)
        
        run_stats = {'processed': 0, 'sent': 0, 'errors': 0}
        
        for handler in self.handlers:
            try:
                logger.info(f"\n Traitement du compte : {handler.config.email_address}")
                
                unread_emails = handler.get_unread_emails(self.max_emails_per_run)
                
                for email_msg in unread_emails:
                    run_stats['processed'] += 1
                    self.stats['total_processed'] += 1
                    
                    if handler.process_email(email_msg):
                        run_stats['sent'] += 1
                        self.stats['total_sent'] += 1
                    else:
                        run_stats['errors'] += 1
                        self.stats['total_errors'] += 1
                    
                    # Pause entre les envois
                    time.sleep(2)
                
            except Exception as e:
                logger.error(f" Erreur lors du traitement du compte : {e}")
                run_stats['errors'] += 1
                self.stats['total_errors'] += 1
        
        logger.info("\n" + "=" * 70)
        logger.info(f" Statistiques de cette exécution:")
        logger.info(f"   ├─ Emails traités : {run_stats['processed']}")
        logger.info(f"   ├─ Réponses envoyées : {run_stats['sent']}")
        logger.info(f"   └─ Erreurs : {run_stats['errors']}")
        logger.info(f" Statistiques totales:")
        logger.info(f"   ├─ Total traités : {self.stats['total_processed']}")
        logger.info(f"   ├─ Total envoyés : {self.stats['total_sent']}")
        logger.info(f"   └─ Total erreurs : {self.stats['total_errors']}")
        logger.info("=" * 70)
    
    def run_continuous(self, interval_minutes: int = 5):
        """Exécute le script en continu"""
        logger.info(f" Mode continu activé (intervalle: {interval_minutes} minutes)")
        logger.info("   Appuyez sur Ctrl+C pour arrêter\n")
        
        try:
            while True:
                self.process_all_emails()
                logger.info(f"\n Prochaine vérification dans {interval_minutes} minutes...\n")
                time.sleep(interval_minutes * 60)
        
        except KeyboardInterrupt:
            logger.info("\n Arrêt du script demandé...")
            self.cleanup()
    
    def run_once(self):
        """Exécute le script une seule fois"""
        logger.info(" Mode exécution unique")
        self.process_all_emails()
        self.cleanup()
    
    def cleanup(self):
        """Nettoie les connexions"""
        logger.info(" Fermeture des connexions...")
        for handler in self.handlers:
            handler.disconnect()
        logger.info(" Terminé proprement")


def main():
    """Fonction principale"""
    # --- Parsing des arguments CLI (pour systemd / lancement non-interactif) ---
    parser = argparse.ArgumentParser(description='Automatisation d\'emails avec Ollama')
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--continuous', action='store_true',
                            help='Mode continu : vérifie les emails périodiquement (recommandé pour systemd)')
    mode_group.add_argument('--once', action='store_true',
                            help='Mode unique : traite les emails une seule fois puis quitte')
    args = parser.parse_args()

    print("=" * 70)
    print("AUTOMATISATION D'EMAILS AVEC OLLAMA")
    print("=" * 70)
    
    try:
        # Charger la configuration
        config = ConfigLoader.load_config(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        )

        # Charger les prompts
        prompts = ConfigLoader.load_prompts(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prompts.json')
        )
        
        # Créer les configurations email
        email_configs = ConfigLoader.create_email_configs(config)
        
        # Initialiser le client Ollama
        ollama_config = config.get('ollama', {})
        ollama_client = OllamaClient(
            base_url=ollama_config.get('base_url', 'http://localhost:11434'),
            model=ollama_config.get('model', 'gemma3:4b'),
            prompts=prompts
        )
        
        # Créer l'automatisation
        automation_config = config.get('automation', {})
        automation = EmailAutomation(
            email_configs,
            ollama_client,
            max_emails_per_run=automation_config.get('max_emails_per_run', 50)
        )
        
        # Configurer les connexions
        if not automation.setup():
            logger.error("Échec de l'initialisation. Vérifiez vos configurations.")
            sys.exit(1)
        
        # --- Sélection du mode ---
        if args.continuous:
            # Mode non-interactif (systemd)
            interval = automation_config.get('check_interval_minutes', 5)
            automation.run_continuous(interval_minutes=interval)
        elif args.once:
            # Mode non-interactif unique
            automation.run_once()
        else:
            # Mode interactif (lancement manuel)
            print("\nMode d'exécution :")
            print("  1. Exécution unique (une fois)")
            print("  2. Exécution continue (vérification périodique)")
            choice = input("\nVotre choix (1 ou 2) : ").strip()
            if choice == '1':
                automation.run_once()
            elif choice == '2':
                interval = automation_config.get('check_interval_minutes', 5)
                automation.run_continuous(interval_minutes=interval)
            else:
                logger.error("Choix invalide")
                automation.cleanup()
    
    except FileNotFoundError:
        logger.error("Fichier config.json introuvable. Créez-le d'abord.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur fatale : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
