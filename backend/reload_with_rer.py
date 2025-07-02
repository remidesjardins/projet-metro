#!/usr/bin/env python3
"""
Script pour effacer le cache et recharger les données avec les RER.
"""

import os
import shutil
import sys
from pathlib import Path

def clear_cache():
    """Efface tous les fichiers de cache."""
    print("🧹 Effacement du cache...")
    
    # Chemin vers le dossier cache
    cache_dir = Path(__file__).parent / 'data' / 'cache'
    
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            print(f"✅ Cache effacé: {cache_dir}")
        except Exception as e:
            print(f"❌ Erreur lors de l'effacement du cache: {e}")
            return False
    else:
        print(f"ℹ️  Dossier cache non trouvé: {cache_dir}")
    
    # Créer le dossier cache vide
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Dossier cache recréé: {cache_dir}")
    
    return True

def reload_data():
    """Recharge les données avec les RER."""
    print("\n🔄 Rechargement des données avec les RER...")
    
    try:
        # Importer après avoir effacé le cache
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from utils.data_manager import DataManager
        
        # Forcer le rechargement
        DataManager.clear_cache()
        
        # Charger les données (cela va recréer le cache avec les RER)
        print("📊 Chargement des données GTFS...")
        graph, positions, stations = DataManager.get_data()
        
        print(f"✅ Données rechargées avec succès!")
        print(f"   - Stations: {len(stations)}")
        print(f"   - Connexions: {sum(len(neighbors) for neighbors in graph.values()) // 2}")
        
        # Compter les lignes
        line_counts = {}
        for station_id, station_data in stations.items():
            lines = station_data['line'] if isinstance(station_data['line'], list) else [station_data['line']]
            for line in lines:
                line_counts[line] = line_counts.get(line, 0) + 1
        
        print(f"   - Lignes disponibles: {sorted(line_counts.keys())}")
        
        # Vérifier les RER
        rer_lines = ['A', 'B', 'C', 'D', 'E']
        found_rer = [line for line in rer_lines if line in line_counts]
        
        if found_rer:
            print(f"   🚆 RER intégrés: {found_rer}")
            for line in found_rer:
                print(f"     * RER {line}: {line_counts[line]} stations")
        else:
            print(f"   ⚠️  Aucun RER trouvé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du rechargement: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale."""
    print("🚆 Intégration des RER dans le système")
    print("=" * 50)
    
    # 1. Effacer le cache
    if not clear_cache():
        print("❌ Impossible d'effacer le cache")
        return False
    
    # 2. Recharger les données
    if not reload_data():
        print("❌ Impossible de recharger les données")
        return False
    
    print("\n🎉 Intégration des RER terminée avec succès!")
    print("\nProchaines étapes:")
    print("1. Redémarrer le serveur backend: python app.py")
    print("2. Tester l'intégration: python test_rer_integration.py")
    print("3. Vérifier l'affichage dans le frontend")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 