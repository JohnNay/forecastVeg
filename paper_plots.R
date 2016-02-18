# "Forecasting Vegetation Health at High Spatial Resolution"

library(dplyr)
load_large_files_on_ornette <- T
saving_data <- baseline <- all_non_scatters <- T

if(load_large_files_on_ornette){
  ## Forecasting Hold-out Data
  rmse <- function(x, y) sqrt( mean( (x - y)^2) )
  
  # install.packages("hexbin")
  
  # Spectral data was the best on training so we used it as the predictor vars in holdout
  load_prep <- function(fp, landuse, missing_middle_row = TRUE){
    if(missing_middle_row) skip <- 1 else skip <- 0
    df <- read.csv(fp,
                   stringsAsFactors = FALSE, header = TRUE,
                   skip = skip)
    if(missing_middle_row){
      # There is one missing row in the exact middle of the data from having
      # to split the data into two pieces and bind back together
      # to get it from h2o into python, bc the data is too big to do it all at once.
      print(df[nrow(df)/2+1,])
      df[nrow(df)/2+1,] <- rep(NA, ncol(df))
      stopifnot(sum(complete.cases(df)) == nrow(df) - 1)
      df <- df[complete.cases(df), ]
    }
    
    for(i in c(1,2,4,5,6)) {
      df[,i] <- as.numeric(df[,i])
    }
    
    landchar <- rep(NA, nrow(df))
    df$landuse <- as.integer(df$landuse)
    for(i in seq(nrow(df))){
      landchar[i] <- landuse[which(landuse$V1 == df$landuse[i]), "V2"]
    }
    df$landuse <- landchar
    df
  }
  
  CA_land <- read.delim(textConnection("11	Water
12	Other
21	Urban
22	Urban
23	Urban
24	Urban
31	Other
41	Forest
42	Forest
43	Forest
51	Scrub
52	Scrub
71	Scrub
72	Scrub
73	Lichens
74	Other
81	Agriculture
82	Agriculture
90	Other
95	Other"), header=FALSE, stringsAsFactors=FALSE)
  SL_land <- read.delim(textConnection("21	Water
3	Forest
17	Scrub
5	Scrub
4	Agriculture
8	Agriculture
20	Urban
1	Other
0 Other
2	Other
6	Other
7	Other
9	Other
10	Other
11	Other
12	Other
13	Other
14	Other
15	Other
16	Other
18	Other
19	Other"), sep = "", header=FALSE, stringsAsFactors=FALSE)
  
  create_time_measure <- function(df, model_name){
    group_by(df, time_period) %>% 
      summarise(RMSE = rmse(predict, EVI),
                Cor = cor(predict, EVI, use = "everything", method = c("pearson")),
                Number = n()) %>% 
      mutate(Model = model_name)
  }
  create_land_measure <- function(df, model_name){
    group_by(df, landuse) %>% 
      summarise(RMSE = rmse(predict, EVI),
                Cor = cor(predict, EVI, use = "everything", method = c("pearson")),
                Number = n()) %>% 
      mutate(Model = model_name)
  }
  create_both_measure <- function(df, model_name){
    group_by(df, time_period, landuse) %>% 
      summarise(RMSE = rmse(predict, EVI),
                Cor = cor(predict, EVI, use = "everything", method = c("pearson")),
                Number = n()) %>% 
      mutate(Model = model_name)
  }
  create_time_measure_both <- function(dfs, model_names = c("GBM", "Baseline")){
    a <- create_time_measure(dfs[[1]], model_name = model_names[1])
    b <- create_time_measure(dfs[[2]], model_name = model_names[2])
    out <- rbind(a, b)
    stopifnot(sum(complete.cases(out)) == nrow(out))
    return(out)
  }
  create_land_measure_both <- function(dfs, model_names = c("GBM", "Baseline")){
    a <- create_land_measure(dfs[[1]], model_name = model_names[1])
    b <- create_land_measure(dfs[[2]], model_name = model_names[2])
    out <- rbind(a, b)
    stopifnot(sum(complete.cases(out)) == nrow(out))
    return(out)
  }
  create_both_measure_both <- function(dfs, model_names = c("GBM", "Baseline")){
    a <- create_both_measure(dfs[[1]], model_name = model_names[1])
    b <- create_both_measure(dfs[[2]], model_name = model_names[2])
    out <- rbind(a, b)
    stopifnot(sum(complete.cases(out)) == nrow(out))
    return(out)
  }
  
  sl <- load_prep("/data/john/srilanka/gbm_predicted_holdoutS.csv", SL_land)
  if(baseline){
    sl_b <- load_prep("/data/john/srilanka/baseline_predicted_holdout.csv", SL_land,
                      missing_middle_row = FALSE)
    colnames(sl_b)[which(colnames(sl_b)=="Pred")] <- "predict"
  }
  
  if(saving_data){
    time_sl_all <- create_time_measure_both(list(sl, sl_b))
    save(time_sl_all, file = "output/time_sl_all.Rda")
    land_sl_all <- create_land_measure_both(list(sl, sl_b))
    save(land_sl_all, file = "output/land_sl_all.Rda")
    both_sl_all <- create_both_measure_both(list(sl, sl_b))
    save(both_sl_all, file = "output/both_sl_all.Rda")
  }
  
  ca <- load_prep("/data/john/CA/gbm_predicted_holdoutS.csv", CA_land)
  if(baseline){
    ca_b <- load_prep("/data/john/CA/baseline_predicted_holdout.csv", CA_land,
                      missing_middle_row = FALSE)
    colnames(ca_b)[which(colnames(ca_b)=="Pred")] <- "predict"
  }
  
  if(saving_data){
    time_ca_all <- create_time_measure_both(list(ca, ca_b))
    save(time_ca_all, file = "output/time_ca_all.Rda")
    land_ca_all <- create_land_measure_both(list(ca, ca_b))
    save(land_ca_all, file = "output/land_ca_all.Rda")
    both_ca_all <- create_both_measure_both(list(ca, ca_b))
    save(both_ca_all, file = "output/both_ca_all.Rda")
  }
  
  nsl <- nrow(sl)
  nca <- nrow(ca)
  # cor_all <- cor(gbm$predict, gbm$EVI, use = "everything" , method = c("pearson"))
  
  # More Holdout Plots - Large Scatter Plots showing predicted and actual values
  source("util_funcs/plot_predicts.R")
  library(ggplot2)
  # SL
  p <- filter(sl, landuse == "Agriculture") %>%
    plot_predicts("SL Agricultural Land EVI ")
  pdf(paste0("output/paper_plots/scatter_sl.pdf"), width=12, height=12)
  print(p)
  dev.off()
  jpeg(paste0("output/paper_plots/scatter_sl.jpg"), width=12, height=12, units = "in", res=300)
  print(p)
  dev.off()
  
  if(baseline){
    p <- filter(sl_b, landuse == "Agriculture") %>%
      plot_predicts("SL Agricultural Land EVI ")
    pdf(paste0("output/paper_plots/scatter_sl_b.pdf"), width=12, height=12)
    print(p)
    dev.off()
    jpeg(paste0("output/paper_plots/scatter_sl_b.jpg"), width=12, height=12, units = "in", res=300)
    print(p)
    dev.off()
  }
  
  # CA
  p <- filter(ca, landuse == "Agriculture") %>%
    plot_predicts("CA Agricultural Land EVI ")
  pdf(paste0("output/paper_plots/scatter_ca.pdf"), width=12, height=12)
  print(p)
  dev.off()
  jpeg(paste0("output/paper_plots/scatter_ca.jpg"), width=12, height=12, units = "in", res=300)
  print(p)
  dev.off()
  
  if(baseline){
    p <- filter(ca_b, landuse == "Agriculture") %>%
      plot_predicts("CA Agricultural Land EVI ")
    pdf(paste0("output/paper_plots/scatter_ca_b.pdf"), width=12, height=12)
    print(p)
    dev.off()
    jpeg(paste0("output/paper_plots/scatter_ca_b.jpg"), width=12, height=12, units = "in", res=300)
    print(p)
    dev.off()
  }
} else {
  nsl <- "36,831,863" # nrow(sl)
  nca <- "61,681,296" # nrow(ca)
}

if(all_non_scatters){
  # If previously saved, can run the next section from the small files in local repo /output directory
  load("output/both_ca_all.Rda")
  load("output/land_ca_all.Rda")
  load("output/time_ca_all.Rda")
  load("output/both_sl_all.Rda")
  load("output/land_sl_all.Rda")
  load("output/time_sl_all.Rda")
  
  titles <- FALSE # No ggtitles for the paper
  labels <- TRUE # labels for the CA and SL (A., B.)
  
  # Replace time periods with nice labels:
  x <- c("Jan", " ", "Feb", " ", "Mar", " ", "April", " ", "May", " ", "June", " ", "July",
         " ", "Aug", " ", "Sept", " ", "Oct", " ", "Nov", " ", "Dec")
  
  # SL
  library(ggplot2)
  p <- ggplot(time_sl_all, aes(x = time_period, y = Cor, group = Model, color = Model)) +
    geom_point() + geom_line() + theme_classic() + 
    theme(legend.position=c(0.5, 0.5)) +
    scale_x_discrete(breaks=1:23,
                     labels=x) +
    scale_colour_brewer(palette = "Dark2") +
    ylab("Correlation between Predicted and Actual") +
    xlab("Time Period") + ylim(c(0,1)) 
  if (titles) p <- p + ggtitle(paste0("Correlation Between Predicted and Actual\nin Sri Lanka Holdout Data n=", nsl))
  
  pdf(paste0("output/paper_plots/time_sl.pdf"), width=7, height=7)
  print(p)
  dev.off()
  
  jpeg(paste0("output/paper_plots/time_sl.jpg"), width=7, height=7, units = "in", res=300)
  print(p)
  dev.off() 
  
  p <- ggplot(land_sl_all,
              aes(x = landuse, y = Cor, fill = Number)) +
    geom_bar(stat = "identity") + theme_classic() + 
    theme(legend.position=c(0.15, 0.8)) +
    scale_fill_continuous(name = "Number of\nObservations") +
    #scale_fill_distiller(name = "Number of\nObservations") +
    facet_grid(~Model) + ylim(c(0,1)) +
    ylab("Correlation between Predicted and Actual") +
    xlab("Land Use")
  if (titles) p <- p + ggtitle(paste0("Correlation Between Predicted and Actual\nin Sri Lanka Holdout Data n=", nsl))
  if(labels) p <- p + annotation_custom(grid::grobTree(grid::textGrob("B.", x=0.9,  y=0.95, hjust=0,
                                                                      gp=grid::gpar(col="black", fontsize=15, fontface="bold"))))
  
  pdf(paste0("output/paper_plots/land_sl.pdf"), width=7.5, height=7)
  print(p)
  dev.off()
  
  jpeg(paste0("output/paper_plots/land_sl.jpg"), width=7.5, height=7, units = "in", res=300)
  print(p)
  dev.off() 
  
  p <- both_sl_all %>% filter(landuse!="Other") %>%
    ggplot(aes(x = time_period, y = Cor, group = landuse, color = landuse)) +
    geom_point() + geom_line() + theme_classic() + 
    theme(legend.position=c(0.15, 0.85),
          legend.title=element_blank()) +
    scale_x_discrete(breaks=1:23,
                     labels=x) +
    scale_colour_brewer(palette = "Dark2") +
    facet_grid(~Model) +
    ylab("Correlation between Predicted and Actual") +
    xlab("Time Period") + 
    ylim(c(min(both_sl_all$Cor),1)) 
  if (titles) p <- p + ggtitle(paste0("Correlation Between Predicted and Actual\nin Sri Lanka Holdout Data n=", nsl))
  if(labels) p <- p + annotation_custom(grid::grobTree(grid::textGrob("B.", x=0.9,  y=0.95, hjust=0,
                                                                      gp=grid::gpar(col="black", fontsize=15, fontface="bold"))))
  
  pdf(paste0("output/paper_plots/time_land_sl.pdf"), width=12, height=7)
  print(p)
  dev.off()
  
  jpeg(paste0("output/paper_plots/time_land_sl.jpg"), width=12, height=7, units = "in", res=300)
  print(p)
  dev.off() 
  
  # Sl specific plot for seasons:
  p <- both_sl_all %>% filter(landuse=="Agriculture", Model=="GBM") %>%
    ggplot(aes(x = time_period, y = Cor)) +
    geom_point() + geom_line() + theme_classic() + 
    scale_x_discrete(breaks=1:23,
                     labels=x) +
    scale_colour_brewer(palette = "Dark2") +
    ylab("Correlation between Predicted and Actual") +
    geom_vline(xintercept=c(4,7,16,19), linetype="dotted") +
    xlab("Time Period") + 
    ylim(c(min(both_sl_all$Cor),1)) +
    ggtitle(paste0("Correlation Between Predicted and Actual\nin Sri Lanka Holdout Data n=", nsl)) +
    annotate("text", x = c(4,7,16,19), 
             y = c(0.4, 0.5, 0.5, 0.4),
             label = c("Maha End", "Yala Start", "Yala End", "Maha Start"), 
             fontface=c("bold", "plain", "plain", "bold"),
             size = c(5))
  
  pdf(paste0("output/paper_plots/seasons_sl.pdf"), width=7, height=7)
  print(p)
  dev.off()
  
  jpeg(paste0("output/paper_plots/seasons_sl.jpg"), width=7, height=7, units = "in", res=300)
  print(p)
  dev.off() 
  
  # CA
  p <- ggplot(time_ca_all, aes(x = time_period, y = Cor, group = Model, color = Model)) +
    geom_point() + geom_line() + theme_classic() + 
    theme(legend.position=c(0.5, 0.2)) +
    scale_x_discrete(breaks=1:23,
                     labels=x) +
    scale_colour_brewer(palette = "Dark2") +
    ylab("Correlation between Predicted and Actual") +
    xlab("Time Period") + ylim(c(0,1))
  if (titles) p <- p +  ggtitle(paste0("Correlation Between Predicted and Actual\nin CA Holdout Data n=", nca))
  
  pdf(paste0("output/paper_plots/time_ca.pdf"), width=7, height=7)
  print(p)
  dev.off()
  
  jpeg(paste0("output/paper_plots/time_ca.jpg"), width=7, height=7, units = "in", res=300)
  print(p)
  dev.off() 
  
  p <- ggplot(land_ca_all,
              aes(x = landuse, y = Cor, fill = Number)) +
    geom_bar(stat = "identity") + theme_classic() + 
    theme(legend.position=c(0.15, 0.8)) +
    scale_fill_continuous(name = "Number of\nObservations") +
    facet_grid(~Model) + ylim(c(0,1)) +
    ylab("Correlation between Predicted and Actual") +
    xlab("Land Use")
  if (titles) p <- p + ggtitle(paste0("Correlation Between Predicted and Actual\nin CA Holdout Data n=", nca))
  if(labels) p <- p + annotation_custom(grid::grobTree(grid::textGrob("A.", x=0.9,  y=0.95, hjust=0,
                                                                      gp=grid::gpar(col="black", fontsize=15, fontface="bold"))))
  
  pdf(paste0("output/paper_plots/land_ca.pdf"), width=7.5, height=7)
  print(p)
  dev.off()
  
  jpeg(paste0("output/paper_plots/land_ca.jpg"), width=7.5, height=7, units = "in", res=300)
  print(p)
  dev.off() 
  
  p <- both_ca_all %>% filter(landuse!="Other") %>%
    ggplot(aes(x = time_period, y = Cor, group = landuse, color = landuse)) +
    geom_point() + geom_line() + theme_classic() + 
    theme(legend.position=c(0.15, 0.85),
          legend.title=element_blank()) +
    scale_x_discrete(breaks=1:23,
                     labels=x) +
    scale_colour_brewer(palette = "Dark2") +
    ylim(c(0,1)) + # ylim(c(min(both_ca_all$Cor),1)) +
    facet_grid(~Model) +
    ylab("Correlation between Predicted and Actual") +
    xlab("Time Period") 
  if (titles) p <- p + ggtitle(paste0("Correlation Between Predicted and Actual\nin CA Holdout Data n=", nca))
  if(labels) p <- p + annotation_custom(grid::grobTree(grid::textGrob("A.", x=0.93,  y=0.95, hjust=0,
                                                                      gp=grid::gpar(col="black", fontsize=15, fontface="bold"))))
  
  pdf(paste0("output/paper_plots/time_land_ca.pdf"), width=12, height=7)
  print(p)
  dev.off()
  
  jpeg(paste0("output/paper_plots/time_land_ca.jpg"), width=12, height=7, units = "in", res=300)
  print(p)
  dev.off() 
  
  # Missing data over time
  cam <- read.csv("output/missing_data/ca_mean.csv", header = FALSE)[,1]
  cas <- read.csv("output/missing_data/ca_std.csv", header = FALSE)[,1]
  slm <- read.csv("output/missing_data/sl_mean.csv", header = FALSE)[,1]
  sls <- read.csv("output/missing_data/sl_std.csv", header = FALSE)[,1]
  
  ca_missing <- data.frame(Mean = cam, SD = cas, Location = "CA",
                           Time = 1:23)
  sl_missing <- data.frame(Mean = slm, SD = sls, Location = "SL",
                           Time = 1:23)
  p <- rbind(ca_missing, sl_missing) %>%
    mutate(min = Mean - SD, max = Mean + SD) %>%
    ggplot(aes(Time, Mean,  group =1)) +
    geom_line() + 
    scale_x_discrete(breaks=1:23,
                     labels=x) +
    geom_ribbon(aes(ymin=min, ymax=max), alpha=0.3) +
    ylim(0,100) + ylab("Mean and SD of Percent of Pixels with Missing Data") +
    facet_grid(~Location) +
    theme_classic()
  if (titles) p <- p + ggtitle("Percent of Pixels with Missing Data Over 23 Periods of the Year")
  
  pdf(paste0("output/paper_plots/missing_data.pdf"), width=7, height=5)
  print(p)
  dev.off()
  jpeg(paste0("output/paper_plots/missing_data.jpg"), width=7, height=5, units = "in", res=300)
  print(p)
  dev.off()
}
