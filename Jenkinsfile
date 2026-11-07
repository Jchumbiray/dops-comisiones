pipeline {
    agent any
    triggers { pollSCM('H/2 * * * *') }   // alternativa al webhook de GitHub cuando Jenkins corre en local
    options { timestamps(); timeout(time: 30, unit: 'MINUTES'); buildDiscarder(logRotator(numToKeepStr: '10')) }
    environment {
        DB_HOST = 'mgg.vps.webdock.cloud'
        DB_PORT = '5432'
        DB_NAME = 'dmc'
        CSV_FILE = 'data/ComisionEmpleados_V1_202610.csv'
    }
    stages {
        stage('CI - Preparar entorno') {
            steps {
                sh 'python3 -m venv .venv && . .venv/bin/activate && pip install -q -r app/requirements.txt pytest'
            }
        }
        stage('CI - Pruebas unitarias') {
            steps { sh '. .venv/bin/activate && pytest -v --junitxml=test-results.xml' }
            post { always { junit 'test-results.xml' } }
        }
        stage('CD - Preparar Blob Storage') {
            steps {
                // Crea los contenedores landing/datalake y deja el CSV en Blob Storage (Azurite en local)
                sh '. .venv/bin/activate && python scripts/seed_blob.py $CSV_FILE'
            }
        }
        stage('CD - Deploy DEV') {
            steps { runEnv('dev') }
        }
        stage('Aprobacion TEST') {
            steps { input message: 'Aprobar despliegue a TEST?', ok: 'Desplegar a TEST' }
        }
        stage('CD - Deploy TEST') {
            steps { runEnv('test') }
        }
        stage('Aprobacion PROD') {
            steps { input message: 'Aprobar despliegue a PRODUCCION?', ok: 'Desplegar a PROD' }
        }
        stage('CD - Deploy PROD') {
            steps { runEnv('prod') }
        }
    }
    post {
        success { echo 'Pipeline completado: DEV, TEST y PROD desplegados.' }
        failure { echo 'El pipeline fallo. Revisar el log de la etapa.' }
    }
}

def runEnv(String envName) {
    withCredentials([usernamePassword(credentialsId: 'dmc-db', usernameVariable: 'DB_USER', passwordVariable: 'DB_PASSWORD')]) {
        sh ". .venv/bin/activate && python app/main.py --env ${envName} --csv \$CSV_FILE"
    }
    sh ". .venv/bin/activate && python scripts/validate_output.py ${envName}"
    archiveArtifacts artifacts: "output/${envName}/*.parquet", fingerprint: true
}
