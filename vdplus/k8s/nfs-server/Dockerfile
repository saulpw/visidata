FROM quay.io/kubernetes_incubator/nfs-provisioner:v2.2.1-k8s1.12

ARG DO_SPACES_API_ID
ENV DO_SPACES_API_ID $DO_SPACES_API_ID
ARG DO_SPACES_API_SECRET
ENV DO_SPACES_API_SECRET $DO_SPACES_API_SECRET

RUN pip3 install s3cmd

ADD s3cfg /root/.s3cfg
ADD run.sh /root/run.sh

ENTRYPOINT ["/root/run.sh"]
