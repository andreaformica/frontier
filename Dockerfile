FROM registry.cern.ch/docker.io/tomcat:9.0

RUN mkdir -p /usr/local/tomcat/webapps/atlr
COPY build/dist/Frontier.war /usr/local/tomcat/webapps/atlr/Frontier.war
COPY context.xml /usr/local/tomcat/conf/Catalina/localhost/atlr.xml
RUN chown -R tomcat:tomcat /usr/local/tomcat
RUN chmod -R 755 /usr/local/tomcat/webapps/atlr
EXPOSE 8080
CMD ["catalina.sh", "run"]
