#!/bin/bash

# MetroCity - Script de lancement de l'audit de performance
# Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins

echo "🚀 MetroCity - Audit de Performance et Impact Écologique"
echo "============================================================"

# Vérification que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérification que le backend existe
if [ ! -d "backend" ]; then
    echo "❌ Le dossier backend n'existe pas. Exécutez ce script depuis la racine du projet."
    exit 1
fi

# Installation des dépendances si nécessaire
if [ ! -f "audit_venv/bin/activate" ]; then
    echo "📦 Création de l'environnement virtuel pour l'audit..."
    python3 -m venv audit_venv
    source audit_venv/bin/activate
    echo "📥 Installation des dépendances..."
    pip install -r requirements_audit.txt
    pip install -r backend/requirements.txt
else
    echo "✅ Environnement virtuel existant trouvé"
    source audit_venv/bin/activate
fi

# Vérification que le serveur backend est démarré
echo "🔍 Vérification du serveur backend..."
if ! curl -s http://localhost:5050/health > /dev/null; then
    echo "⚠️  Le serveur backend n'est pas démarré."
    echo "💡 Démarrage automatique du serveur backend..."
    
    # Démarrage du serveur en arrière-plan
    cd backend
    python app.py &
    BACKEND_PID=$!
    cd ..
    
    # Attente que le serveur soit prêt
    echo "⏳ Attente du démarrage du serveur..."
    for i in {1..30}; do
        if curl -s http://localhost:5050/health > /dev/null; then
            echo "✅ Serveur backend prêt!"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            echo "❌ Impossible de démarrer le serveur backend"
            kill $BACKEND_PID 2>/dev/null
            exit 1
        fi
    done
else
    echo "✅ Serveur backend en cours d'exécution"
    BACKEND_PID=""
fi

# Nettoyage des anciens rapports
echo "🧹 Nettoyage des anciens rapports..."
rm -f AUDIT_PERFORMANCE_RAPPORT.md
rm -f audit_performance_data.json

# Lancement de l'audit
echo ""
echo "🔬 Lancement de l'audit de performance..."
echo "============================================================"
cd "$(dirname "$0")"
python3 audit_performance.py "$@"

# Vérification que l'audit s'est bien déroulé
if [ -f "AUDIT_PERFORMANCE_RAPPORT.md" ]; then
    echo ""
    echo "============================================================"
    echo "✅ Audit terminé avec succès!"
    echo "📄 Rapport généré: AUDIT_PERFORMANCE_RAPPORT.md"
    echo "📊 Données JSON: audit_performance_data.json"
    echo ""
    echo "📖 Pour consulter le rapport:"
    echo "   cat AUDIT_PERFORMANCE_RAPPORT.md"
    echo "   ou ouvrez le fichier dans votre éditeur préféré"
    echo ""
else
    echo "❌ L'audit a échoué. Vérifiez les logs ci-dessus."
    exit 1
fi

# Nettoyage du serveur backend si on l'a démarré
if [ ! -z "$BACKEND_PID" ]; then
    echo "🛑 Arrêt du serveur backend..."
    kill $BACKEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
fi

echo "🎉 Audit terminé!" 