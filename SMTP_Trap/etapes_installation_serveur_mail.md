# Étapes pour mettre en place un serveur de messagerie multi-domaine

Voici les étapes nécessaires pour configurer votre propre serveur de messagerie capable de recevoir des emails pour plusieurs domaines et d'être consulté via Thunderbird.

## 1. Préparation des Noms de Domaine (DNS)
Pour chaque nom de domaine que vous possédez (ex: `mondomaine1.com`, `mondomaine2.fr`), vous devez configurer les enregistrements DNS chez votre registrar (OVH, GoDaddy, etc.) :
*   **Enregistrement A** : Faites pointer un sous-domaine (ex: `mail.mondomaine1.com`) vers l'adresse IP publique de votre serveur.
*   **Enregistrement MX (Mail Exchange)** : Indiquez que les emails pour `@mondomaine1.com` doivent être envoyés vers `mail.mondomaine1.com`. Répétez pour chaque domaine.
*   **SPF (Sender Policy Framework)** : Ajoutez un enregistrement TXT pour autoriser votre serveur à envoyer des emails (optionnel pour la réception pure, recommandé).

## 2. Préparation du Serveur
*   Avoir un serveur Linux (VPS ou dédié) avec une adresse IP fixe.
*   Ouvrir les ports nécessaires dans le pare-feu :
    *   **Port 25 (SMTP)** : Pour recevoir les emails des autres serveurs.
    *   **Port 143 (IMAP)** ou **993 (IMAPS)** : Pour que Thunderbird puisse lire les emails.
    *   **Port 587 (Submission)** ou **465 (SMTPS)** : Pour envoyer des emails depuis Thunderbird (si besoin).

## 3. Installation du Serveur de Réception (MTA - SMTP)
Vous devez installer un logiciel "MTA" (Mail Transfer Agent) comme **Postfix**.
*   Configurer Postfix pour écouter sur l'interface publique.
*   Lui indiquer la liste de tous vos domaines (Virtual Domains) pour qu'il accepte les emails destinés à chacun d'eux.
*   Configurer le routage pour stocker les emails reçus dans des dossiers spécifiques sur le disque dur.

## 4. Installation du Serveur de Lecture (MDA - IMAP)
Pour lire vos emails avec Thunderbird, vous avez besoin d'un logiciel qui parle le langage IMAP, comme **Dovecot**.
*   Configurer Dovecot pour aller lire les emails là où Postfix les a déposés.
*   Activer l'authentification (login/mot de passe) pour sécuriser l'accès à vos boîtes mail.

## 5. Sécurisation (Certificats SSL/TLS)
*   Installer **Certbot (Let's Encrypt)** pour obtenir un certificat de sécurité gratuit pour votre nom de domaine principal (ex: `mail.mondomaine1.com`).
*   Configurer Postfix et Dovecot pour utiliser ces certificats, afin que les connexions soient chiffrées (le petit cadenas).

## 6. Création des Utilisateurs / Boîtes Mail
*   Créer les comptes utilisateurs sur le serveur ou dans une base de données virtuelle.
*   Associer chaque utilisateur à son adresse email (ex: `contact@mondomaine1.com`, `info@mondomaine2.fr`).

## 7. Configuration du Client (Thunderbird)
*   Ouvrir Thunderbird sur votre ordinateur.
*   Ajouter un nouveau compte de messagerie.
*   Renseigner votre adresse email et votre mot de passe.
*   Configurer les serveurs :
    *   **Serveur entrant (IMAP)** : `mail.mondomaine1.com` (Port 993 SSL/TLS).
    *   **Serveur sortant (SMTP)** : `mail.mondomaine1.com` (Port 587 STARTTLS).
*   Thunderbird va maintenant synchroniser et afficher vos emails.

Votre serveur est maintenant prêt à recevoir et stocker les emails de tous vos domaines !
