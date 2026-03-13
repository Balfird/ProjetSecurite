# Analyse avancée des mails du serveur

Date du relevé : 13 mars 2026

Source analysée : `/var/mail/vhosts`

Périmètre :

- analyse effectuée sur `1 953` messages stockés dans les dossiers Maildir `cur/` et `new/`
- les statistiques de langue, mots-clés et spam/phishing sont heuristiques
- une date aberrante `2006-01` a été trouvée dans au moins un en-tête `Date` mal formé ou atypique

## 1. Répartition par domaine destinataire

| Domaine | Messages | Part |
|---|---:|---:|
| `next-wireless.co` | 650 | 33.28 % |
| `atvm94.org` | 488 | 24.99 % |
| `newaircraftsolution.com` | 307 | 15.72 % |
| `anne-gerard.net` | 296 | 15.16 % |
| `yolan.dev` | 87 | 4.45 % |
| `ergo-concepts.fr` | 74 | 3.79 % |
| `11laposte.net` | 32 | 1.64 % |
| `senghor.me` | 10 | 0.51 % |
| `esthetiqueautopropre.com` | 9 | 0.46 % |

Lecture rapide :

- `next-wireless.co` et `atvm94.org` concentrent à eux deux `1 138` messages, soit `58.27 %` du trafic stocké.

## 2. Évolution temporelle

### Par mois

| Mois | Messages |
|---|---:|
| `2006-01` | 1 |
| `2026-02` | 118 |
| `2026-03` | 1 834 |

### Par semaine ISO

| Semaine | Messages |
|---|---:|
| `2026-W10` | 1 032 |
| `2026-W11` | 792 |
| `2026-W09` | 67 |
| `2026-W07` | 36 |
| `2026-W08` | 25 |
| `2006-W01` | 1 |

### Principaux jours de pic

| Jour | Messages |
|---|---:|
| `2026-03-07` | 639 |
| `2026-03-09` | 294 |
| `2026-03-10` | 194 |
| `2026-03-08` | 181 |
| `2026-03-11` | 146 |
| `2026-03-06` | 142 |
| `2026-03-12` | 102 |
| `2026-03-13` | 56 |

Lecture rapide :

- le trafic explose en mars 2026
- un pic majeur apparaît le `7 mars 2026` avec `639` messages
- les semaines `2026-W10` et `2026-W11` concentrent l’essentiel de l’activité

## 3. Doublons ou campagnes répétitives

### Sujets les plus répétés

| Sujet | Occurrences |
|---|---:|
| `Re: No-reply.` | 93 |
| `Action requise – Mise à jour de votre compte` | 79 |
| `Re: Se han filtrado sus datos personales debido a ciertas actividades en sitios sospechosos.` | 74 |
| `DERNIER RAPPEL AVANT TRANSMISSION AU COMMISSAIRE DE JUSTICE` | 65 |
| `Nоuvеllе Dеmаndе ѕur vоtrе ϲоmрtе` | 64 |
| `Mise à jour obligatoire` | 46 |
| `Mise à jour de livraison - Mondial Relay` | 40 |
| `Suivi de dossier – Paiement en attente de régularisation` | 32 |
| `New Auto Insurance Rates Now Starting at $59/month` | 26 |
| `Re: Re: Se han filtrado sus datos personales debido a ciertas actividades en sitios sospechosos.` | 24 |

### Doublons forts par expéditeur + sujet + taille

| Expéditeur | Sujet normalisé | Taille | Occurrences |
|---|---|---:|---:|
| `paiementantaiservices@windsipe.o12.pl` | `suivi de dossier – paiement en attente de régularisation` | 11880 | 15 |
| `noreply@mondialrelay.fr` | `mise à jour de livraison - mondial relay` | 4417 | 9 |
| `sumup-ltd@chamsswitch.com` | `mise à jour obligatoire` | 7452 | 8 |
| `contact@next-wireless.co` | `no-reply.` | 1788 | 6 |
| `portail-antai@chamsswitch.com` | `dernier rappel avant transmission au commissaire de justice` | 11185 | 6 |
| `portail-antai.fr@chamsswitch.com` | `dernier rappel avant transmission au commissaire de justice` | 11182 | 6 |

Lecture rapide :

- plusieurs campagnes répétitives sont visibles, notamment autour de faux paiements, faux rappels administratifs et fausses mises à jour de compte
- la répétition stricte `expéditeur + sujet + taille` suggère des envois de campagne automatisés plutôt que des messages légitimes isolés

## 4. Top expéditeurs

### Top adresses expéditrices

| Expéditeur | Messages |
|---|---:|
| `contact@next-wireless.co` | 359 |
| `contact@atvm94.org` | 235 |
| `sumup@chamsswitch.com` | 79 |
| `googlealerts-noreply@google.com` | 74 |
| `noreply@mondialrelay.fr` | 60 |
| `sumup-ltd@chamsswitch.com` | 46 |
| `noreply-dmarc-support@google.com` | 34 |
| `b-stock@alerts.bstock.com` | 29 |
| `portail-antai@chamsswitch.com` | 27 |
| `portail-antai.fr@chamsswitch.com` | 26 |

### Top domaines expéditeurs

| Domaine expéditeur | Messages |
|---|---:|
| `next-wireless.co` | 450 |
| `atvm94.org` | 236 |
| `chamsswitch.com` | 190 |
| `google.com` | 114 |
| `mondialrelay.fr` | 60 |
| `alerts.bstock.com` | 29 |
| `gmail.com` | 24 |
| `vmi3037245.contaboserver.net` | 22 |
| `hubx.com` | 18 |
| `windsipe.o12.pl` | 16 |

Lecture rapide :

- une part importante des messages provient des domaines hébergés localement eux-mêmes, ce qui peut correspondre à des réponses, tests ou rebonds
- `chamsswitch.com` ressort fortement parmi les sources externes répétitives

## 5. Répartition par langue estimée

| Langue estimée | Messages | Part |
|---|---:|---:|
| Français | 1 042 | 53.35 % |
| Espagnol | 600 | 30.72 % |
| Anglais | 238 | 12.19 % |
| Inconnue | 69 | 3.53 % |
| Allemand | 4 | 0.20 % |

Remarque :

- cette détection est fondée sur des mots fréquents dans l’objet et un extrait du corps ; elle donne une tendance, pas une classification linguistique exacte

## 6. Mots-clés dominants

| Mot-clé | Messages |
|---|---:|
| `facture` | 292 |
| `compte` | 271 |
| `document` | 228 |
| `notification` | 174 |
| `paiement` | 159 |
| `banque` | 134 |
| `code` | 91 |
| `account` | 90 |
| `livraison` | 84 |
| `payment` | 44 |
| `delivery` | 35 |
| `commande` | 16 |
| `otp` | 13 |
| `bank` | 13 |

Lecture rapide :

- les thèmes dominants sont clairement administratifs, financiers et liés aux comptes utilisateurs
- cela correspond bien à des campagnes de phishing classiques : paiement, compte, document, notification, banque, livraison

## 7. Part probable de spam ou phishing

Heuristique utilisée :

- mots-clés suspects dans le sujet
- échecs SPF/DKIM/DMARC visibles dans les en-têtes
- divergence `Reply-To` / `From`
- domaines à TLD fréquemment abusés
- liens combinés à des mots-clés de compte ou mot de passe
- lexique d’arnaque financière

### Résultat global

| Indicateur | Messages | Part |
|---|---:|---:|
| Spam probable (`score >= 2`) | 207 | 10.60 % |
| Phishing probable (`score >= 3`) | 30 | 1.54 % |

### Répartition des scores heuristiques

| Score | Messages |
|---|---:|
| `0` | 1 197 |
| `1` | 549 |
| `2` | 177 |
| `3` | 25 |
| `4` | 5 |

### Signaux les plus fréquents

| Signal heuristique | Occurrences |
|---|---:|
| `subject_keyword` | 326 |
| `reply_to_mismatch` | 175 |
| `auth_fail` | 124 |
| `payment_scam_keyword` | 100 |
| `link_plus_account_keyword` | 79 |
| `suspicious_tld` | 35 |

Conclusion rapide :

- le stock contient une part non négligeable de messages probablement malveillants ou au minimum douteux
- les campagnes les plus visibles imitent :
  - des services de paiement
  - des services de livraison
  - des procédures administratives ou de justice
  - des mises à jour de compte
