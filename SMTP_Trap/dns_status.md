# Statut de la Configuration DNS des Noms de Domaine

Ce document résume l'état de la propagation des enregistrements DNS (SPF, DMARC, et DKIM) pour vos trois domaines liés au serveur.

| Nom de Domaine | SPF (@) | DMARC (_dmarc) | DKIM (default._domainkey) | Boite mail IMAP |
| :--- | :---: | :---: | :---: | :---: |
| **anne-gerard.net** | ⚠️ Espace en trop | ✅ OK | ✅ OK | ✅ OK |
| **11laposte.net** | ⚠️ Espace en trop | ✅ OK | ✅ OK | ✅ OK |
| **esthetiqueautopropre.com** | ⚠️ Espace en trop | ✅ OK | ✅ OK | ✅ OK |
| **ergo-concepts.fr** | ✅ OK | ✅ OK | ✅ OK | ✅ OK |
| **newaircraftsolution.com** | ⚠️ Espace en trop | ✅ OK | ✅ OK | ✅ OK |
| **atvm94.org** | ⚠️ Espace en trop | ⚠️ Espace dans l'adresse | ✅ OK | ✅ OK |
| **next-wireless.co** | ⏳ Manquant | ✅ OK | ✅ OK | ✅ OK |
| **yolan.dev** | ⚠️ Espace en trop | ✅ OK | ✅ OK | ✅ OK |
| **senghor.me** | ⚠️ Espace en trop | ✅ OK | ✅ OK | ✅ OK |

---

### Explications :
* **✅ Fait / Propagé :** L'enregistrement est configuré correctement et est déjà visible sur internet pour les fournisseurs d'email (comme Google ou Microsoft).
* **⏳ En attente... :** L'enregistrement n'est pas encore visible. Cela peut être dû au délai normal de propagation DNS (qui peut prendre de quelques minutes à quelques heures), ou parce qu'il n'a pas encore été renseigné dans la zone DNS de votre hébergeur.

_Dernière vérification effectuée automatiquement sur le serveur via les commandes `dig`._
