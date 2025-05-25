#FROM registry.cern.ch/docker.io/tomcat:9.0
FROM tomcat:9.0

## RUN mkdir -p /usr/local/tomcat/webapps/atlr
COPY build/dist/Frontier.war /usr/local/tomcat/webapps/atlr.war
COPY context.xml /usr/local/tomcat/conf/context.xml
EXPOSE 8080
CMD ["catalina.sh", "run"]
