package gov.fnal.frontier;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.FilterConfig;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;

import java.io.IOException;
import java.time.Instant;

import net.logstash.logback.marker.Markers;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

public class FrontierRequestFilter implements Filter {

    private static final Logger log = LoggerFactory.getLogger(FrontierRequestFilter.class);

    @Override
    public void init(FilterConfig filterConfig) throws ServletException {
        // Initialization code if needed
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        HttpServletRequest httpRequest = (HttpServletRequest) request;
        long startTime = System.currentTimeMillis();
        MDC.put("token", "frontier");
        MDC.put("requestURI", httpRequest.getRequestURI());
        MDC.put("requestQuery", httpRequest.getQueryString() != null ?
                "?" + httpRequest.getQueryString() :
                "");
        MDC.put("startTime", String.valueOf(startTime));
        // Log request details
        log.debug("Filter request start: {} {} ",
                Instant.now(),
                httpRequest.getMethod()
        );

        try {
            chain.doFilter(request, response);
        } finally {
            // Log processing time
            long duration = System.currentTimeMillis() - startTime;
            MDC.put("duration", String.valueOf(duration));
            String queryTimeMillisec = MDC.get("queryTime");
            String dbRow = MDC.get("dbRows");
            String dbDataTime = MDC.get("dbDataTime");
            log.info("Filter request completed! ");
            // Optionally, you can log the response status if needed
            // Better approach using LogstashMarkers:
            log.info(Markers.append("durationMillisec", duration)
                            .and(Markers.append("queryTimeMillisec",
                                    Long.valueOf(queryTimeMillisec)))
                            .and(Markers.append("dbRows", Long.valueOf(dbRow)))
                            .and(Markers.append("dbDataTime", Long.valueOf(dbDataTime))),
                    "Message with typed fields");
            MDC.clear();
        }
    }

    @Override
    public void destroy() {
        // Cleanup code if needed
    }
}