# Statistiques des boîtes mail du serveur

Date du relevé : 13 mars 2026

Source analysée : `/var/mail/vhosts`

Méthode :

- `INBOX principal` = messages présents dans `cur/` et `new/` à la racine de la boîte Maildir
- `Messages reçus estimés` = tous les messages stockés dans la boîte, hors dossiers `Sent` et `Drafts`
- `Messages stockés` = tous les messages présents dans tous les dossiers Maildir

## Totaux globaux

| Indicateur | Valeur |
|---|---:|
| Nombre de boîtes mail présentes | 9 |
| Total INBOX principal | 1 256 |
| Total messages reçus estimés | 1 942 |
| Total messages stockés | 1 952 |
| Total messages envoyés | 9 |
| Total messages en corbeille | 652 |
| Total brouillons | 1 |
| Taille totale occupée | 75.8 MiB |

## Détail par boîte

| Boîte mail | INBOX principal | Messages reçus estimés | Messages stockés | Envoyés | Corbeille | Brouillons | Taille |
|---|---:|---:|---:|---:|---:|---:|---:|
| `contact@11laposte.net` | 22 | 27 | 32 | 5 | 5 | 0 | 616.0 KiB |
| `contact@anne-gerard.net` | 215 | 292 | 296 | 3 | 43 | 1 | 29.5 MiB |
| `contact@atvm94.org` | 429 | 487 | 487 | 0 | 58 | 0 | 18.1 MiB |
| `contact@ergo-concepts.fr` | 70 | 74 | 74 | 0 | 4 | 0 | 3.1 MiB |
| `contact@esthetiqueautopropre.com` | 8 | 9 | 9 | 0 | 1 | 0 | 612.7 KiB |
| `contact@newaircraftsolution.com` | 159 | 307 | 307 | 0 | 148 | 0 | 11.6 MiB |
| `contact@next-wireless.co` | 261 | 650 | 650 | 0 | 389 | 0 | 8.5 MiB |
| `contact@senghor.me` | 8 | 9 | 10 | 1 | 1 | 0 | 249.9 KiB |
| `contact@yolan.dev` | 84 | 87 | 87 | 0 | 3 | 0 | 3.7 MiB |

## Lecture rapide

- Si l'on parle de mails actuellement reçus et conservés sur l'ensemble des boîtes, le total est de `1 942`.
- Si l'on parle de tous les messages stockés, y compris envoyés et brouillons, le total est de `1 952`.
- Les boîtes les plus chargées sont `contact@next-wireless.co` (`650` messages stockés) et `contact@atvm94.org` (`487` messages stockés).
