#!/usr/bin/env python3
"""
VirusTotal Hash Checker
Calcule le hash d'un fichier et vérifie sur VirusTotal

https://docs.virustotal.com/reference/file-info
alternative
https://virustotal.github.io/vt-py/quickstart.html
"""

import sys
import os
import hashlib
import requests
import json
import argparse
from datetime import datetime


def calculate_sha256(filepath):
    """Calcule le hash SHA256 d'un fichier"""
    sha256_hash = hashlib.sha256()
    
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def get_file_info(filepath):
    """Récupère les informations détaillées du fichier"""
    stats = os.stat(filepath)
    
    info = {
        'nom': os.path.basename(filepath),
        'chemin': os.path.abspath(filepath),
        'taille': stats.st_size,
        'taille_kb': stats.st_size / 1024,
        'taille_mb': stats.st_size / (1024 * 1024),
        'modifie': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'cree': datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
        'extension': os.path.splitext(filepath)[1]
    }
    
    return info


def check_virustotal(file_hash, api_key):
    """Vérifie le hash sur VirusTotal"""
    url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
    headers = {
        "accept": "application/json",
        "x-apikey": api_key
    }
    
    response = requests.get(url, headers=headers)
    return response.status_code, response.json()


def save_report(data, file_hash, filepath):
    """Sauvegarde le rapport JSON dans un fichier"""
    # Génère un nom de fichier basé sur le hash et la date
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"vt_report_{os.path.basename(filepath)}_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filename


def display_file_info(info):
    """Affiche les informations du fichier"""
    print("=" * 70)
    print("INFORMATIONS DU FICHIER")
    print("=" * 70)
    print(f"Nom:              {info['nom']}")
    print(f"Chemin complet:   {info['chemin']}")
    print(f"Extension:        {info['extension'] if info['extension'] else 'Aucune'}")
    print(f"Taille:           {info['taille']:,} octets ({info['taille_kb']:.2f} KB / {info['taille_mb']:.2f} MB)")
    print(f"Date création:    {info['cree']}")
    print(f"Date modification: {info['modifie']}")
    print("=" * 70)


def main():
    # Configuration du parseur d'arguments
    parser = argparse.ArgumentParser(
        description='VirusTotal Hash Checker - Vérifie un fichier sur VirusTotal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  %(prog)s fichier.exe
  %(prog)s fichier.exe --api-key VOTRE_CLE
  %(prog)s fichier.exe --report
  %(prog)s fichier.exe --api-key VOTRE_CLE --report
        """
    )
    
    parser.add_argument('fichier', help='Chemin du fichier à analyser')
    parser.add_argument('--api-key', '-k', 
                       help='Clé API VirusTotal (ou utilisez la variable VT_API_KEY)')
    parser.add_argument('--report', '-r', action='store_true',
                       help='Sauvegarder le rapport JSON complet dans un fichier')
    
    args = parser.parse_args()
    
    # Récupération de l'API key
    api_key = args.api_key or os.environ.get('VT_API_KEY')
    
    if not api_key:
        print("Erreur: Clé API non fournie")
        print("  Solution 1: export VT_API_KEY='votre_cle'")
        print("  Solution 2: python script.py <fichier> --api-key <votre_cle>")
        sys.exit(1)
    
    filepath = args.fichier
    
    # Vérification de l'existence du fichier
    if not os.path.exists(filepath):
        print(f"Erreur: Le fichier '{filepath}' n'existe pas")
        sys.exit(1)
    
    # Récupération et affichage des infos du fichier
    file_info = get_file_info(filepath)
    display_file_info(file_info)
    
    # Calcul du hash
    print(f"\nCalcul du hash SHA256...")
    file_hash = calculate_sha256(filepath)
    print(f"Hash SHA256: {file_hash}\n")
    
    # Vérification sur VirusTotal
    print("Vérification sur VirusTotal...")
    status_code, data = check_virustotal(file_hash, api_key)
    
    print(f"Status Code: {status_code}\n")
    
    # Sauvegarde du rapport si demandé
    if args.report:
        report_file = save_report(data, file_hash, filepath)
        print(f" Rapport JSON sauvegardé: {report_file}\n")
    
    if status_code == 200:
        # Navigation sécurisée dans le JSON
        attributes = data.get('data', {}).get('attributes', {})
        stats = attributes.get('last_analysis_stats', {})
        
        if stats:
            print("=" * 70)
            print("RÉSULTATS DE L'ANALYSE VIRUSTOTAL")
            print("=" * 70)
            
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            harmless = stats.get('harmless', 0)
            undetected = stats.get('undetected', 0)
            total = malicious + suspicious + harmless + undetected
            
            print(f"Moteurs d'analyse:  {total}")
            print(f"   Malveillant:   {malicious}")
            print(f"   Suspect:       {suspicious}")
            print(f"   Inoffensif:    {harmless}")
            print(f"   Non détecté:   {undetected}")
            
            print("\n" + "=" * 70)
            if malicious > 0:
                print(f"  VERDICT: FICHIER MALVEILLANT ({malicious}/{total} détections)")
            elif suspicious > 0:
                print(f"  VERDICT: FICHIER SUSPECT ({suspicious}/{total} détections)")
            else:
                print(f"VERDICT: FICHIER PROBABLEMENT SÛR")
            print("=" * 70)
            
            # Informations supplémentaires si disponibles
            if attributes.get('last_analysis_date'):
                date = datetime.fromtimestamp(attributes['last_analysis_date']).strftime('%Y-%m-%d %H:%M:%S')
                print(f"\nDernière analyse: {date}")
            
            if attributes.get('type_description'):
                print(f"Type de fichier:  {attributes['type_description']}")
        else:
            print("\nRéponse complète:")
            print(data)
    elif status_code == 404:
        print("Fichier non trouvé dans la base VirusTotal")
        print("   Le fichier n'a jamais été analysé auparavant")
    else:
        print(f"\nErreur: {data}")


if __name__ == "__main__":
    main()
