pipeline {
    agent { label 'small' }
    environment {
      imagename = "ghcr.io/pilotdataplatform/metadata"
      commit = sh(returnStdout: true, script: 'git describe --always').trim()
      registryCredential = 'pilot-ghcr'
      dockerImage = ''
    }

    stages {

    stage('DEV Git clone') {
        when { branch 'develop' }
        steps {
            git branch: 'develop',
                url: 'https://github.com/PilotDataPlatform/metadata.git',
                credentialsId: 'pilot-gh'
        }
    }

    stage('DEV Build and push image') {
      when {branch "develop"}
      steps {
        script {
            docker.withRegistry('https://ghcr.io', registryCredential) {
                customImage = docker.build('$imagename:alembic-$commit-CAC', '--target alembic-image .')
                customImage.push()
            }
            docker.withRegistry('https://ghcr.io', registryCredential) {
                customImage = docker.build('$imagename:metadata-$commit-CAC', '--target metadata-image .')
                customImage.push()
            }
        }
      }
    }

    stage('DEV Remove image') {
      when {branch "develop"}
      steps {
            sh 'docker rmi $imagename:alembic-$commit-CAC'
            sh 'docker rmi $imagename:metadata-$commit-CAC'
      }
    }

    stage('DEV Deploy') {
      when {branch "develop"}
      steps{
        build(job: "/VRE-IaC/UpdateAppVersion", parameters: [
          [$class: 'StringParameterValue', name: 'TF_TARGET_ENV', value: 'dev' ],
          [$class: 'StringParameterValue', name: 'TARGET_RELEASE', value: 'metadata' ],
          [$class: 'StringParameterValue', name: 'NEW_APP_VERSION', value: "$commit-CAC" ]
        ])
      }
    }

    stage('STAGING Git clone') {
        when { branch 'main' }
        steps {
            git branch: 'main',
                url: 'https://git.indocresearch.org/pilot/metadata.git',
                credentialsId: 'lzhao'
        }
    }

    stage('STAGING Build and push image') {
      when {branch "main"}
      steps {
        script {
            docker.withRegistry('https://ghcr.io', registryCredential) {
                customImage = docker.build('$imagename:alembic-$commit', '--target alembic-image .')
                customImage.push()
            }
            docker.withRegistry('https://ghcr.io', registryCredential) {
                customImage = docker.build('$imagename:metadata-$commit', '--target metadata-image .')
                customImage.push()
            }
        }
      }
    }

    stage('STAGING Remove image') {
      when {branch "main"}
      steps {
            sh 'docker rmi $imagename:alembic-$commit'
            sh 'docker rmi $imagename:metadata-$commit'
      }
    }

    stage('STAGING Deploy') {
      when {branch "main"}
      steps{
        build(job: "/VRE-IaC/Staging-UpdateAppVersion", parameters: [
          [$class: 'StringParameterValue', name: 'TF_TARGET_ENV', value: 'staging' ],
          [$class: 'StringParameterValue', name: 'TARGET_RELEASE', value: 'metadata' ],
          [$class: 'StringParameterValue', name: 'NEW_APP_VERSION', value: "$commit" ]
        ])
      }
    }
  }
  post {
      failure {
        slackSend color: '#FF0000', message: "Build Failed! - ${env.JOB_NAME} $commit  (<${env.BUILD_URL}|Open>)", channel: 'jenkins-dev-staging-monitor'
      }
  }

}
