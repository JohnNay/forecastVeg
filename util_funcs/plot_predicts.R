plot_predicts <- function(x, outcome= NULL, verbose=TRUE){
  rreal <- range(x$EVI)
  rpredict <- range(x$predict)
  r <- c(min(rreal, rpredict), max(rreal, rpredict))
  p2 <- ggplot2::ggplot(x, ggplot2::aes(x=predict,y=EVI)) +
    ggplot2::geom_bin2d(bins = 900) +
    ggplot2::geom_density2d(color = "yellow") +
    ggplot2::geom_abline(intercept=0, slope=1, colour="darkorange", linetype="dashed") + 
    #   scale_colour_gradient( low="red", high="white")
    #   scale_fill_brewer(palette="BuPu")
    #   scale_colour_gradient2() +
    #geom_point(alpha = 0.005) +
    ggplot2::ylab(paste0("Actual ", outcome ," (n=", nrow(x) ,")")) + 
    ggplot2::xlab(paste0("Predicted ", outcome ," (n=", nrow(x) ,")")) + 
    ggplot2::ylim(r) + ggplot2::xlim(r) +
    ggplot2::theme_classic() +
    ggplot2::theme(legend.title=ggplot2::element_blank(), 
                   legend.justification=c(0,1), legend.position=c(0,1),
                   text = ggplot2::element_text(size=20)) 
  if(verbose) message("Done with ggplot, now adding the marginal plots.")
  return(ggExtra::ggMarginal(p2,
                      type = 'histogram',
                      margins = 'both',
                      size = 5,
                      col = '#10B07D',
                      fill = '#0ACC7F'))
}
