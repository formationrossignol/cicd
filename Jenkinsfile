node {
    // Variables adaptées pour macOS
    def APP_NAME = 'python-app'
    def DEPLOY_PATH = "${env.HOME}/deployed-apps/python-app"
    def LOG_FILE = "${env.HOME}/deployed-apps/logs/python-app.log"
    def BUILD_VERSION = "${BUILD_NUMBER}_${new Date().format('yyyyMMdd_HHmmss')}"
    
    try {
        stage('Checkout') {
            echo 'Récupération du code source...'
            echo "Workspace: ${env.WORKSPACE}"
            echo "Home directory: ${env.HOME}"
            echo "Build version: ${BUILD_VERSION}"
            
            sh 'ls -la'
            
            def pyFiles = sh(script: 'find . -maxdepth 1 -name "*.py" | wc -l', returnStdout: true).trim()
            if (pyFiles == '0') {
                echo "⚠️  Aucun fichier Python trouvé à la racine"
                echo "Création d'une application Flask de TEST avec debug..."
                sh '''
                    cat > app.py << 'EOF'
from flask import Flask, jsonify
import os
import sys
from datetime import datetime
import logging

# Configuration des logs
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    logger.info("Route / appelée")
    return jsonify({
        'message': '🎉 Application Python déployée avec succès !',
        'version': os.environ.get('DEPLOY_VERSION', 'unknown'),
        'timestamp': datetime.now().isoformat(),
        'status': 'running',
        'port': os.environ.get('PORT', 'unknown'),
        'python_version': sys.version,
        'pid': os.getpid()
    })

@app.route('/health')
def health():
    logger.info("Health check appelé")
    return jsonify({
        'status': 'healthy',
        'version': os.environ.get('DEPLOY_VERSION', 'unknown'),
        'port': os.environ.get('PORT', 'unknown')
    })

@app.route('/debug')
def debug():
    return jsonify({
        'environment_variables': dict(os.environ),
        'current_directory': os.getcwd(),
        'python_path': sys.path[:5]  # Premiers éléments seulement
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 Démarrage de l'application sur le port {port}")
    logger.info(f"🏠 Répertoire de travail: {os.getcwd()}")
    logger.info(f"🐍 Version Python: {sys.version}")
    
    # Force le host à 0.0.0.0 pour être accessible depuis l'extérieur
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
EOF
                    
                    cat > requirements.txt << 'EOF'
Flask==3.1.1
EOF
                    
                    echo "✅ Application Flask de TEST créée avec debug"
                '''
            }
        }
        
        stage('Setup Python Environment') {
            echo 'Configuration de l\'environnement Python...'
            sh '''
                echo "=== Vérification Python ==="
                python3 --version
                pip3 --version
                
                echo "=== Création environnement virtuel ==="
                if [ -d "venv" ]; then
                    rm -rf venv
                fi
                
                python3 -m venv venv
                source venv/bin/activate
                
                echo "=== Mise à jour pip ==="
                python -m pip install --upgrade pip
                
                echo "=== Installation dépendances ==="
                if [ -f "requirements.txt" ]; then
                    pip install -r requirements.txt
                    echo "Dépendances installées depuis requirements.txt"
                else
                    echo "Installation Flask par défaut"
                    pip install flask
                fi
                
                echo "=== Packages installés ==="
                pip list
            '''
        }
        
        stage('Pre-Deploy Diagnostic') {
            echo 'Diagnostic pré-déploiement...'
            sh '''
                echo "=== DIAGNOSTIC SYSTÈME ==="
                echo "🖥️  Système: $(uname -a)"
                echo "👤 Utilisateur: $(whoami)"
                echo "🏠 Home: $HOME"
                echo "💽 Espace disque:"
                df -h $HOME
                
                echo "=== PORTS UTILISÉS ==="
                echo "🔍 Ports en écoute:"
                lsof -i -P | grep LISTEN | head -10
                
                echo "=== PROCESSUS PYTHON EXISTANTS ==="
                ps aux | grep python | grep -v grep || echo "Aucun processus Python"
                
                echo "=== RÉSEAU ==="
                echo "🌐 Interface réseau:"
                ifconfig | grep -A1 "lo0\\|en0" || echo "Pas d'info réseau"
            '''
        }
        
        stage('Deploy') {
            echo 'Déploiement de l\'application...'
            
            sh '''
                echo "=== ARRÊT DE L'APPLICATION EXISTANTE ==="
                pkill -f python-app 2>/dev/null || echo "Aucun processus python-app trouvé"
                sleep 2
                
                echo "=== PRÉPARATION RÉPERTOIRES ==="
                mkdir -p ''' + DEPLOY_PATH + '''
                mkdir -p ''' + "${env.HOME}/deployed-apps/logs" + '''
                
                # Backup avec horodatage
                if [ -d "''' + DEPLOY_PATH + '''" ] && [ "$(ls -A ''' + DEPLOY_PATH + ''' 2>/dev/null)" ]; then
                    BACKUP_DIR="''' + "${env.HOME}/deployed-apps/backups" + '''/python-app-$(date +%Y%m%d_%H%M%S)"
                    mkdir -p $(dirname $BACKUP_DIR)
                    cp -r ''' + DEPLOY_PATH + ''' $BACKUP_DIR
                    echo "✅ Sauvegarde créée: $BACKUP_DIR"
                fi
                
                rm -rf ''' + DEPLOY_PATH + '''/*
                
                echo "=== COPIE APPLICATION ==="
                cp -r dist/* ''' + DEPLOY_PATH + '''/
                
                echo "=== CONFIGURATION ENVIRONNEMENT ==="
                cd ''' + DEPLOY_PATH + '''
                
                python3 -m venv venv
                source venv/bin/activate
                pip install --upgrade pip
                
                if [ -f "requirements.txt" ]; then
                    pip install -r requirements.txt
                else
                    pip install flask
                fi
                
                chmod +x *.py
                
                echo "=== RECHERCHE PORT LIBRE AVEC DIAGNOSTIC ==="
                find_free_port() {
                    for port in 8080 8081 8082 8083 8084 8085 3000 3001 4000 4001 9000 9001; do
                        echo "🔍 Test du port $port..." >&2
                        if ! lsof -i :$port > /dev/null 2>&1; then
                            echo "✅ Port $port libre" >&2
                            echo $port  # Retourne SEULEMENT le numéro de port
                            return
                        else
                            echo "❌ Port $port occupé par:" >&2
                            lsof -i :$port >&2
                        fi
                    done
                    echo "⚠️  Aucun port libre trouvé, utilisation de 8080" >&2
                    echo 8080
                }
                
                FREE_PORT=$(find_free_port)
                echo "🎯 Port sélectionné: $FREE_PORT"
                
                echo "=== CONFIGURATION APPLICATION ==="
                cat > deploy_config.py << EOF
import os
ENVIRONMENT = "dev"
PORT = $FREE_PORT
DEBUG = True  # Activé pour diagnostic
DEPLOY_VERSION = "''' + BUILD_VERSION + '''"
DEPLOY_PATH = "''' + DEPLOY_PATH + '''"
LOG_FILE = "''' + LOG_FILE + '''"

# Variables d'environnement
os.environ['DEPLOY_VERSION'] = DEPLOY_VERSION
os.environ['PORT'] = str(PORT)
os.environ['FLASK_ENV'] = 'development'
EOF
                
                echo "=== CRÉATION SCRIPT DE LANCEMENT AVEC DEBUG ==="
                cat > start_app.sh << EOF
#!/bin/bash
set -e  # Arrêt si erreur

echo "🚀 Démarrage de l'application Python..."
echo "📁 Répertoire: \$(pwd)"
echo "🕐 Heure: \$(date)"

cd ''' + DEPLOY_PATH + '''
source venv/bin/activate

# Variables d'environnement avec debug
export PYTHONPATH="''' + DEPLOY_PATH + ''':$PYTHONPATH"
export DEPLOY_VERSION="''' + BUILD_VERSION + '''"
export PORT=$FREE_PORT
export FLASK_ENV=development
export PYTHONUNBUFFERED=1  # Logs immédiats

echo "🔧 Variables d'environnement:"
echo "PORT=\$PORT"
echo "DEPLOY_VERSION=\$DEPLOY_VERSION"
echo "PYTHONPATH=\$PYTHONPATH"

echo "🐍 Version Python dans venv:"
python --version

echo "📦 Packages Flask:"
pip show flask

echo "📄 Fichiers présents:"
ls -la *.py

# Test d'import Flask
echo "🧪 Test d'import Flask:"
python -c "import flask; print(f'Flask version: {flask.__version__}')"

echo "🎬 Lancement de l'application..."
if [ -f "app.py" ]; then
    exec python app.py
elif [ -f "main.py" ]; then
    exec python main.py
else
    echo "❌ Aucun fichier d'entrée trouvé"
    exit 1
fi
EOF
                chmod +x start_app.sh
                
                echo "=== DÉMARRAGE APPLICATION AVEC LOGS DÉTAILLÉS ==="
                nohup ./start_app.sh > ''' + LOG_FILE + ''' 2>&1 </dev/null &
                APP_PID=$!
                
                echo "🎯 PID de démarrage: $APP_PID"
                
                # Attendre le démarrage
                echo "⏳ Attente du démarrage (10 secondes)..."
                sleep 10
                
                # Vérifier que le processus existe toujours
                if ps -p $APP_PID > /dev/null 2>&1; then
                    echo $APP_PID > python-app.pid
                    echo "✅ Processus actif (PID: $APP_PID)"
                else
                    echo "❌ ERREUR: Le processus a crashé au démarrage"
                    echo "📄 Logs d'erreur:"
                    cat ''' + LOG_FILE + '''
                    exit 1
                fi
                
                # Scripts utilitaires
                cat > stop_app.sh << EOF
#!/bin/bash
if [ -f python-app.pid ]; then
    PID=\\\$(cat python-app.pid)
    if ps -p \\\$PID > /dev/null 2>&1; then
        echo "🛑 Arrêt de l'application (PID: \\\$PID)"
        kill \\\$PID
        sleep 3
        if ps -p \\\$PID > /dev/null 2>&1; then
            kill -9 \\\$PID
        fi
        rm -f python-app.pid
        echo "✅ Application arrêtée"
    else
        echo "⚠️  Processus déjà arrêté"
        rm -f python-app.pid
    fi
else
    echo "❌ PID file non trouvé"
fi
EOF
                chmod +x stop_app.sh
                
                cat > status_app.sh << EOF
#!/bin/bash
echo "=== STATUT APPLICATION ==="
if [ -f python-app.pid ]; then
    PID=\\\$(cat python-app.pid)
    if ps -p \\\$PID > /dev/null 2>&1; then
        echo "✅ Application active (PID: \\\$PID)"
        ps -p \\\$PID -o pid,ppid,pcpu,pmem,command
    else
        echo "❌ Application arrêtée"
    fi
else
    echo "❌ PID file non trouvé"
fi

echo "🔍 Processus Python:"
ps aux | grep python | grep -v grep

echo "🌐 Ports en écoute:"
lsof -i -P | grep LISTEN | grep $FREE_PORT || echo "Port $FREE_PORT pas en écoute"

echo "📄 Logs récents:"
tail -10 ''' + LOG_FILE + ''' 2>/dev/null || echo "Pas de logs"
EOF
                chmod +x status_app.sh
                
                echo $FREE_PORT > deployed_port.txt
                echo "📄 Logs: ''' + LOG_FILE + '''"
                echo "🌐 URL: http://localhost:$FREE_PORT"
                echo "📊 Statut: cd ''' + DEPLOY_PATH + ''' && ./status_app.sh"
            '''
        }
        
        stage('Comprehensive Health Check') {
            echo 'Vérification complète de l\'application...'
            sh '''
                echo "=== DIAGNOSTIC COMPLET ==="
                
                cd ''' + DEPLOY_PATH + '''
                
                # Vérifier PID
                if [ -f "python-app.pid" ]; then
                    PID=$(cat python-app.pid)
                    if ps -p $PID > /dev/null 2>&1; then
                        echo "✅ Processus actif (PID: $PID)"
                        echo "📊 Détails du processus:"
                        ps -p $PID -o pid,ppid,pcpu,pmem,etime,command
                    else
                        echo "❌ Processus mort"
                        echo "📄 Logs complets:"
                        cat ''' + LOG_FILE + '''
                        exit 1
                    fi
                else
                    echo "❌ PID file manquant"
                    exit 1
                fi
                
                # Vérifier logs
                echo "=== LOGS APPLICATION ==="
                if [ -f "''' + LOG_FILE + '''" ]; then
                    echo "📄 Logs récents (30 dernières lignes):"
                    tail -30 ''' + LOG_FILE + '''
                    echo ""
                else
                    echo "❌ Fichier de log manquant"
                fi
                
                # Vérifier port
                APP_PORT=$(cat deployed_port.txt 2>/dev/null || echo "8080")
                echo "=== VÉRIFICATION PORT $APP_PORT ==="
                
                if lsof -i :$APP_PORT > /dev/null 2>&1; then
                    echo "✅ Port $APP_PORT en écoute"
                    echo "📡 Processus utilisant le port:"
                    lsof -i :$APP_PORT
                else
                    echo "❌ Port $APP_PORT PAS en écoute"
                    echo "🔍 Tous les ports en écoute:"
                    lsof -i -P | grep LISTEN
                    exit 1
                fi
                
                # Tests de connectivité progressifs
                echo "=== TESTS DE CONNECTIVITÉ ==="
                
                echo "🧪 Test 1: Ping localhost"
                ping -c 1 localhost || echo "Ping échoué"
                
                echo "🧪 Test 2: Telnet sur le port"
                (echo > /dev/tcp/localhost/$APP_PORT) 2>/dev/null && echo "✅ Port accessible" || echo "❌ Port inaccessible"
                
                echo "🧪 Test 3: Tests HTTP avec curl"
                SUCCESS=false
                for i in 1 2 3 4 5; do
                    echo "Tentative HTTP $i/5 sur http://localhost:$APP_PORT"
                    
                    if command -v curl > /dev/null; then
                        RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" --max-time 10 http://localhost:$APP_PORT/ 2>&1)
                        HTTP_CODE=$(echo "$RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
                        
                        if [ "$HTTP_CODE" = "200" ]; then
                            echo "✅ Application répond correctement (HTTP 200)"
                            echo "📡 Réponse:"
                            echo "$RESPONSE" | sed 's/HTTP_CODE:[0-9]*$//'
                            SUCCESS=true
                            break
                        else
                            echo "⚠️  Réponse HTTP: $HTTP_CODE"
                            echo "📡 Contenu: $RESPONSE"
                        fi
                    else
                        echo "❌ Curl non disponible"
                    fi
                    
                    if [ $i -lt 5 ]; then
                        echo "⏳ Attente 5 secondes..."
                        sleep 5
                    fi
                done
                
                if [ "$SUCCESS" = true ]; then
                    echo "🎉 APPLICATION FONCTIONNE PARFAITEMENT !"
                    
                    echo "🧪 Test des endpoints supplémentaires:"
                    curl -s http://localhost:$APP_PORT/health && echo ""
                    curl -s http://localhost:$APP_PORT/debug | head -5 && echo ""
                    
                else
                    echo "❌ APPLICATION NON ACCESSIBLE VIA HTTP"
                    echo "🔍 DIAGNOSTIC FINAL:"
                    echo "Processus:"
                    ps aux | grep python
                    echo "Ports:"
                    netstat -an | grep LISTEN | grep $APP_PORT || echo "Port pas trouvé dans netstat"
                    echo "Logs complets:"
                    cat ''' + LOG_FILE + '''
                fi
                
                echo ""
                echo "=== RÉSUMÉ ==="
                echo "🏠 Répertoire: ''' + DEPLOY_PATH + '''"
                echo "📄 Logs: ''' + LOG_FILE + '''"
                echo "🌐 Port: $APP_PORT"
                echo "🆔 PID: $(cat python-app.pid 2>/dev/null || echo 'N/A')"
                echo "📊 Statut: ./status_app.sh"
                echo "🛑 Arrêt: ./stop_app.sh"
            '''
        }
        
        // Récupérer le port pour le message final
        def deployedPort = "8080"
        try {
            deployedPort = sh(script: "cat ${DEPLOY_PATH}/deployed_port.txt 2>/dev/null || echo 8080", returnStdout: true).trim()
        } catch (Exception e) {
            deployedPort = "8080"
        }
        
        // Message de succès détaillé
        echo '🎉 Déploiement terminé !'
        echo """
        ===========================================
        ✅ APPLICATION DÉPLOYÉE ET ACTIVE
        ===========================================
        📱 Application: ${APP_NAME}  
        🏷️  Version: ${BUILD_VERSION}
        🏠 Répertoire: ${DEPLOY_PATH}
        📄 Logs: ${LOG_FILE}
        🌐 URL: http://localhost:${deployedPort}
        ===========================================
        
        🧪 TESTS À FAIRE MAINTENANT:
        
        1️⃣ Dans le navigateur:
           http://localhost:${deployedPort}
           http://localhost:${deployedPort}/health
           http://localhost:${deployedPort}/debug
        
        2️⃣ En ligne de commande:
           curl http://localhost:${deployedPort}
           curl http://localhost:${deployedPort}/health
        
        📊 COMMANDES UTILES:
        
        🔍 Vérifier statut:
        cd ${DEPLOY_PATH} && ./status_app.sh
        
        📄 Voir logs en temps réel:
        tail -f ${LOG_FILE}
        
        🛑 Arrêter l'app:
        cd ${DEPLOY_PATH} && ./stop_app.sh
        
        🔄 Redémarrer l'app:
        cd ${DEPLOY_PATH} && ./start_app.sh &
        
        🔍 Voir tous les ports:
        lsof -i -P | grep LISTEN
        
        ⚠️  Si problème persistant, vérifiez:
        1. Les logs: cat ${LOG_FILE}
        2. Le processus: ps aux | grep python
        3. Le port: lsof -i :${deployedPort}
        ===========================================
        """
        
    } catch (Exception e) {
        echo "❌ Erreur durant le déploiement: ${e.getMessage()}"
        
        sh """
            echo "=== DIAGNOSTIC D'ERREUR ==="
            echo "🏠 Home: ${env.HOME}"
            echo "📁 Workspace: \$(pwd)"
            echo "👤 Utilisateur: \$(whoami)"
            
            echo "=== LOGS D'ERREUR ==="
            if [ -f "${LOG_FILE}" ]; then
                echo "📄 Logs de l'application:"
                cat ${LOG_FILE}
            else
                echo "Pas de logs d'application"
            fi
            
            echo "=== PROCESSUS ==="
            ps aux | grep python | grep -v grep || echo "Aucun processus Python"
            
            echo "=== PORTS ==="
            lsof -i -P | grep LISTEN || echo "Aucun port en écoute"
            
            echo "=== RÉPERTOIRES ==="
            ls -la ${env.HOME}/deployed-apps/ 2>/dev/null || echo "Pas de répertoire deployed-apps"
        """
        
        throw e
    } finally {
        echo '🧹 Nettoyage du workspace...'
        sh '''
            rm -rf venv/ || true
            rm -rf __pycache__/ || true
            find . -name "*.pyc" -delete 2>/dev/null || true
        '''
    }
}
