FROM registry.cern.ch/docker.io/tomcat:11.0
## FROM tomcat:11.0

## RUN mkdir -p /usr/local/tomcat/webapps/atlr
COPY build/dist/Frontier.war /usr/local/tomcat/webapps/atlr.war
COPY context.xml /usr/local/tomcat/conf/context.xml
COPY logging.properties /usr/local/tomcat/conf/logging.properties
# Notes: it could be we need to add ojdbc to tomcat lib directory
## unzip ./build/dist/Frontier.war WEB-INF/lib/ojdbc11-21.11.0.0.jar -d /tmp/
## cp /tmp/WEB-INF/lib/ojdbc11-21.11.0.0.jar /usr/local/tomcat/lib/
EXPOSE 8080
#CMD ["catalina.sh", "run"]
ENTRYPOINT ["sh", "-c", "catalina.sh run > /usr/local/tomcat/logs/catalina.out 2>&1"]
