# Documentation de la configuration du serveur mail

Date du relevé : 13 mars 2026
Machine : `vmi3037245.contaboserver.net`

## 1. Vue d'ensemble

Le serveur mail en place repose sur les composants suivants :

- `Postfix` : MTA SMTP principal pour la réception et l'envoi des emails.
- `Dovecot` : service IMAP et backend d'authentification SASL pour Postfix.
- `OpenDKIM` : signature DKIM des emails sortants.
- `smtp-relay.service` : application Go séparée dans `/root/SMTP_Relay`, installée mais actuellement inactive. Ce n'est pas le MTA principal du serveur.

En pratique, la pile mail active est :

1. réception SMTP par `Postfix` sur le port `25`
2. soumission authentifiée par `Postfix` sur le port `587`
3. stockage des boîtes virtuelles dans `/var/mail/vhosts`
4. consultation des boîtes par `Dovecot` en IMAP (`143` et `993`)
5. signature DKIM par `OpenDKIM` via milter local sur `127.0.0.1:8891`

## 2. Services détectés

Services actifs :

- `postfix.service` : activé
- `dovecot.service` : activé et en cours d'exécution
- `opendkim.service` : activé et en cours d'exécution

Service installé mais inactif :

- `smtp-relay.service` : activé mais `inactive (dead)` au moment du relevé

Services non utilisés ici :

- `exim4`
- `sendmail`

## 3. Ports réellement à l'écoute

Ports ouverts localement par les services mail :

- `25/tcp` : SMTP entrant via `Postfix`
- `587/tcp` : submission SMTP via `Postfix`
- `143/tcp` : IMAP via `Dovecot`
- `993/tcp` : IMAPS via `Dovecot`
- `8891/tcp` sur `127.0.0.1` : socket TCP locale `OpenDKIM`

Ports non actifs malgré la présence de blocs de configuration par défaut :

- `110/tcp` : POP3 non exposé
- `995/tcp` : POP3S non exposé
- `465/tcp` : SMTPS/submissions non exposé

## 4. Postfix

Fichiers principaux :

- `/etc/postfix/main.cf`
- `/etc/postfix/master.cf`
- `/etc/postfix/vmailbox`
- `/etc/postfix/virtual`
- `/etc/aliases`
- `/etc/mailname`

### 4.1 Identité Postfix

Valeurs principales :

- `myhostname = vmi3037245.contaboserver.net`
- `myorigin = /etc/mailname`
- contenu de `/etc/mailname` : `vmi3037245.contaboserver.net`
- `mydestination = $myhostname, localhost.$mydomain, localhost`

Conséquence :

- le serveur ne traite en local que son propre hostname et `localhost`
- les domaines métiers sont gérés comme domaines virtuels, pas comme domaines système locaux

### 4.2 Écoute réseau et sécurité SMTP

- `inet_interfaces = all`
- `inet_protocols = all`
- `mynetworks` limité à `127.0.0.0/8`, `::1` et IPv6 loopback
- `smtpd_relay_restrictions = permit_mynetworks permit_sasl_authenticated defer_unauth_destination`

Conséquence :

- le serveur accepte le relais uniquement pour :
  - les connexions locales
  - les utilisateurs authentifiés
- cela évite un open relay dans la configuration actuelle

### 4.3 TLS Postfix

Certificats utilisés :

- certificat : `/etc/letsencrypt/live/mail-all/fullchain.pem`
- clé privée : `/etc/letsencrypt/live/mail-all/privkey.pem`

Paramètres :

- `smtpd_tls_security_level = may`
- `smtp_tls_security_level = may`

Conséquence :

- le chiffrement TLS est proposé mais non imposé sur le port SMTP `25`
- sur le port `587`, `master.cf` force :
  - `smtpd_tls_security_level=encrypt`
  - `smtpd_tls_auth_only=yes`

Donc :

- le port `587` impose TLS avant authentification
- le port `25` accepte le clair si le client distant ne négocie pas TLS

### 4.4 Authentification SMTP

Postfix délègue l'authentification à Dovecot :

- `smtpd_sasl_type = dovecot`
- `smtpd_sasl_path = private/auth`
- `smtpd_sasl_auth_enable = yes`

Le socket utilisé est :

- `/var/spool/postfix/private/auth`

Ce socket est créé côté Dovecot avec :

- `mode = 0666`
- `user = postfix`
- `group = postfix`

### 4.5 Domaines virtuels

`Postfix` gère les domaines suivants comme domaines de boîtes virtuelles :

- `anne-gerard.net`
- `11laposte.net`
- `esthetiqueautopropre.com`
- `ergo-concepts.fr`
- `newaircraftsolution.com`
- `atvm94.org`
- `next-wireless.co`
- `yolan.dev`
- `senghor.me`

Paramètres concernés :

- `virtual_mailbox_domains`
- `virtual_mailbox_base = /var/mail/vhosts`
- `virtual_mailbox_maps = hash:/etc/postfix/vmailbox`
- `virtual_alias_maps = hash:/etc/postfix/virtual`
- `virtual_uid_maps = static:5000`
- `virtual_gid_maps = static:5000`

L'utilisateur système dédié au stockage mail est :

- `vmail` (`uid=5000`, `gid=5000`)

### 4.6 Boîtes et alias

Le fichier `/etc/postfix/vmailbox` définit une boîte réelle `contact@...` pour chaque domaine :

- `contact@anne-gerard.net`
- `contact@11laposte.net`
- `contact@esthetiqueautopropre.com`
- `contact@ergo-concepts.fr`
- `contact@newaircraftsolution.com`
- `contact@atvm94.org`
- `contact@next-wireless.co`
- `contact@yolan.dev`
- `contact@senghor.me`

Le fichier `/etc/postfix/virtual` redirige ensuite tout le domaine vers cette boîte `contact` :

- `@anne-gerard.net -> contact@anne-gerard.net`
- etc. pour chaque domaine

Conséquence :

- toute adresse non explicitement gérée d'un domaine est redirigée vers l'adresse `contact@domaine`
- exemple : `info@anne-gerard.net` ou `bonjour@anne-gerard.net` aboutissent dans `contact@anne-gerard.net`

### 4.7 Aliases système

Dans `/etc/aliases` :

- `postmaster -> root`

Cela concerne les emails système locaux, pas les domaines virtuels métiers.

## 5. Dovecot

Fichiers principaux :

- `/etc/dovecot/dovecot.conf`
- `/etc/dovecot/conf.d/10-mail.conf`
- `/etc/dovecot/conf.d/10-auth.conf`
- `/etc/dovecot/conf.d/10-master.conf`
- `/etc/dovecot/conf.d/10-ssl.conf`
- `/etc/dovecot/users`

### 5.1 Protocoles exposés

Configuration effective (`doveconf -n`) :

- `protocols = " imap"`

Conséquence :

- IMAP est le protocole réellement utilisé
- POP3 n'est pas activé en pratique
- le bloc `submission-login` présent dans la configuration Dovecot n'est pas utilisé ici pour l'envoi, car la soumission SMTP est assurée par Postfix sur `587`

### 5.2 Emplacement des boîtes

- `mail_location = maildir:/var/mail/vhosts/%d/%n`

Exemples observés :

- `/var/mail/vhosts/anne-gerard.net/contact`
- `/var/mail/vhosts/11laposte.net/contact`
- etc.

Chaque boîte est au format `Maildir`.

### 5.3 Base d'authentification

Méthodes autorisées :

- `auth_mechanisms = plain login`

Backend :

- `passdb driver = passwd-file`
- fichier : `/etc/dovecot/users`

Base utilisateur :

- `userdb driver = static`
- `uid = vmail`
- `gid = vmail`
- `home = /var/mail/vhosts/%d/%n`

Observation importante :

- le fichier `/etc/dovecot/users` stocke les mots de passe avec le schéma `{PLAIN}`
- cela signifie que les mots de passe sont enregistrés en clair et non hachés

Il existe actuellement un compte `contact@...` par domaine, avec la même logique d'authentification centralisée dans ce fichier.

### 5.4 TLS Dovecot

Fichiers TLS :

- `ssl = yes`
- `ssl_cert = </etc/letsencrypt/live/mail-all/fullchain.pem`
- `ssl_key = </etc/letsencrypt/live/mail-all/privkey.pem`

Conséquence :

- IMAP peut fonctionner en clair sur `143`
- IMAPS chiffré est disponible sur `993`

Le minimum de version TLS n'est pas explicitement redéfini dans le fichier chargé.

## 6. OpenDKIM

Fichiers principaux :

- `/etc/opendkim.conf`
- `/etc/opendkim/KeyTable`
- `/etc/opendkim/SigningTable`
- `/etc/opendkim/TrustedHosts`

### 6.1 Intégration avec Postfix

`OpenDKIM` écoute sur :

- `inet:8891@localhost`

`Postfix` lui envoie les messages via :

- `smtpd_milters = inet:localhost:8891`
- `non_smtpd_milters = inet:localhost:8891`

Paramètres complémentaires :

- `milter_protocol = 6`
- `milter_default_action = accept`

Conséquence :

- si `OpenDKIM` tombe, Postfix continue d'accepter les messages
- ils peuvent alors partir sans signature DKIM

### 6.2 Domaines signés

Le fichier `SigningTable` active la signature pour tous les expéditeurs des domaines :

- `anne-gerard.net`
- `11laposte.net`
- `esthetiqueautopropre.com`
- `ergo-concepts.fr`
- `newaircraftsolution.com`
- `atvm94.org`
- `next-wireless.co`
- `yolan.dev`
- `senghor.me`

### 6.3 Clé utilisée

Le `KeyTable` montre que chaque domaine utilise le sélecteur :

- `default`

et référence le même fichier de clé privée :

- `/etc/opendkim/keys/mail.private`

Conséquence :

- la configuration actuelle semble réutiliser une même clé DKIM privée pour tous les domaines, avec des enregistrements DNS distincts par domaine mais pointant vers la même clé locale

## 7. Flux fonctionnel

### 7.1 Réception d'un email depuis Internet

1. un serveur distant envoie un message vers ce serveur sur le port `25`
2. `Postfix` accepte le message pour un domaine présent dans `virtual_mailbox_domains`
3. l'adresse est résolue via `virtual_alias_maps` et/ou `virtual_mailbox_maps`
4. le message est livré dans la boîte Maildir sous `/var/mail/vhosts/<domaine>/<utilisateur>`

### 7.2 Envoi par un utilisateur authentifié

1. le client mail se connecte sur `587`
2. TLS est imposé
3. le client s'authentifie via SASL sur Dovecot
4. `Postfix` accepte le relais grâce à `permit_sasl_authenticated`
5. `OpenDKIM` signe le message
6. `Postfix` remet ensuite le mail au serveur distant destinataire

### 7.3 Consultation d'une boîte

1. le client mail se connecte en IMAP `143` ou IMAPS `993`
2. `Dovecot` authentifie l'utilisateur via `/etc/dovecot/users`
3. la boîte Maildir correspondante est ouverte dans `/var/mail/vhosts/%d/%n`

## 8. Application annexe `SMTP_Relay`

Une application distincte existe dans :

- `/root/SMTP_Relay`

Un service systemd existe :

- `/etc/systemd/system/smtp-relay.service`

Caractéristiques observées :

- lance `/root/SMTP_Relay/start.sh`
- répertoire de travail : `/root/SMTP_Relay`
- redémarrage automatique configuré
- service actuellement inactif

Le script `start.sh` :

- charge éventuellement un fichier `.env`
- exécute `go mod tidy`
- installe la dépendance `modernc.org/sqlite`
- compile un binaire `smtp_relay`
- annonce :
  - serveur SMTP sur `:2525`
  - dashboard web sur `http://localhost:8080`

Au moment du relevé, aucun port `2525` ou `8080` n'était à l'écoute, ce qui confirme que cette application n'était pas active.

Conclusion :

- cette application n'est pas le serveur mail principal actuellement utilisé pour les domaines en production
- elle ressemble à un outil séparé de relais/piège SMTP ou de traitement applicatif

## 9. Points sensibles et remarques

### 9.1 Points corrects

- relais SMTP limité aux clients authentifiés ou locaux
- séparation des boîtes via l'utilisateur dédié `vmail`
- DKIM en place pour les domaines configurés
- port `587` correctement forcé en TLS

### 9.2 Points faibles

- les mots de passe Dovecot sont stockés en clair dans `/etc/dovecot/users` avec `{PLAIN}`
- IMAP non chiffré reste accessible sur `143`
- SMTP `25` n'impose pas TLS, même si cela reste fréquent pour l'interopérabilité Internet
- `OpenDKIM` est en `milter_default_action = accept`, donc les mails peuvent sortir non signés si le milter échoue
- une même clé privée DKIM semble réutilisée pour tous les domaines

### 9.3 Ce qui n'est pas visible localement

La machine ne permet pas, via les seuls fichiers locaux, de confirmer :

- les enregistrements DNS `MX`
- les enregistrements `SPF`
- les enregistrements `DKIM` publics publiés
- la politique `DMARC`
- les règles de pare-feu externes éventuelles

Ces éléments doivent être vérifiés côté DNS/hébergeur pour compléter l'audit mail.

## 10. Résumé très court

Le serveur mail actif repose sur `Postfix + Dovecot + OpenDKIM`.

- réception SMTP : `25`
- soumission SMTP authentifiée : `587`
- lecture IMAP : `143` / `993`
- boîtes virtuelles : `/var/mail/vhosts`
- domaines configurés : 9
- boîte principale par domaine : `contact@domaine`
- toutes les autres adresses du domaine sont redirigées vers `contact@domaine`

L'application `/root/SMTP_Relay` existe à côté, mais elle n'est pas active et ne constitue pas le serveur mail principal au moment du relevé.
