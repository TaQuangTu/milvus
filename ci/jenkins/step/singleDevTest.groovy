timeout(time: 120, unit: 'MINUTES') {
    dir ('milvus-helm') {
        sh 'helm version'
        sh 'helm repo add stable https://kubernetes.oss-cn-hangzhou.aliyuncs.com/charts'
        sh 'helm repo update'
        checkout([$class: 'GitSCM', branches: [[name: "${env.HELM_BRANCH}"]], userRemoteConfigs: [[url: "https://github.com/milvus-io/milvus-helm.git", name: 'origin', refspec: "+refs/heads/${env.HELM_BRANCH}:refs/remotes/origin/${env.HELM_BRANCH}"]]])
        // sh 'helm dep update'

        retry(3) {
            try {
                dir ('charts/milvus') {
                    sh "helm install --wait --timeout 300s --set image.repository=registry.zilliz.com/milvus/engine --set persistence.enabled=true --set image.tag=${DOCKER_VERSION} --set image.pullPolicy=Always --set service.type=ClusterIP -f ci/db_backend/mysql_${BINARY_VERSION}_values.yaml -f ci/filebeat/values.yaml --namespace milvus ${env.HELM_RELEASE_NAME} ."
                }
            } catch (exc) {
                def helmStatusCMD = "helm get manifest --namespace milvus ${env.HELM_RELEASE_NAME} | kubectl describe -n milvus -f - && \
                                     kubectl logs --namespace milvus -l \"app=milvus,release=${env.HELM_RELEASE_NAME}\" -c milvus && \
                                     helm status -n milvus ${env.HELM_RELEASE_NAME}"
                def helmResult = sh script: helmStatusCMD, returnStatus: true
                if (!helmResult) {
                    sh "helm uninstall -n milvus ${env.HELM_RELEASE_NAME} && sleep 1m"
                }
                throw exc
            }
        }
    }
    dir ("tests/milvus_python_test") {
        // sh 'python3 -m pip install -r requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com'
        sh 'python3 -m pip install -r requirements.txt'
        sh "python3 -m pip install --index-url https://test.pypi.org/simple/ pymilvus"
        sh "pytest . --alluredir=\"test_out/dev/single/mysql\" --level=1 --ip ${env.HELM_RELEASE_NAME}.milvus.svc.cluster.local --service ${env.HELM_RELEASE_NAME} >> ${WORKSPACE}/${env.DEV_TEST_ARTIFACTS}/milvus_${BINARY_VERSION}_mysql_dev_test.log"
        // sh "pytest test_restart.py --alluredir=\"test_out/dev/single/mysql\" --level=3 --ip ${env.HELM_RELEASE_NAME}.milvus.svc.cluster.local --service ${env.HELM_RELEASE_NAME}"
    }
}
