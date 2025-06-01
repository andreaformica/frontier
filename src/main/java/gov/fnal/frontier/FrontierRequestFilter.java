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
        MDC.put("requestURI", httpRequest.getRequestURI());
        MDC.put("requestQuery", httpRequest.getQueryString() != null ?
                "?" + httpRequest.getQueryString() :
                "");
        MDC.put("startTime", String.valueOf(startTime));
        // Log request details
        log.debug("Filter request: {} {} {} {}",
                Instant.now(),
                httpRequest.getMethod(),
                httpRequest.getRequestURI(),
                httpRequest.getQueryString() != null ? "?" + httpRequest.getQueryString() : ""
        );

        try {
            chain.doFilter(request, response);
        } finally {
            // Log processing time
            long duration = System.currentTimeMillis() - startTime;
            MDC.put("duration", String.valueOf(duration));
            log.debug("Filter request: {} Completed in {} ms", Instant.now(), duration);
            // Optionally, you can log the response status if needed

            MDC.clear();
        }
    }

    @Override
    public void destroy() {
        // Cleanup code if needed
    }
}