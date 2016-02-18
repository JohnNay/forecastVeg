# "Forecasting Vegetation Health at High Spatial Resolution"
form <- function(file, datatype){
  gbm <- read.csv(file = file)
  gbm$Data <- datatype
  gbm <- gbm[complete.cases(gbm), ]
  gbm$Iteration <- seq(nrow(gbm))
  gbm
}

sl <- rbind(form("output/gbmres.csv", "Level 3"),
            form("output/gbmresS.csv", "Spectral"),
            form("output/gbmres_evilt.csv", "Land and Time"),
            form("output/gbmres_evi.csv", "EVI Lag"))
sl$Location <- "SL"
ca <- rbind(form("output/gbmresCA.csv", "Level 3"),
            form("output/gbmresSCA.csv", "Spectral"),
            form("output/gbmresCA_evilt.csv", "Land and Time"),
            form("output/gbmresCA_evi.csv", "EVI Lag"))
ca$Location <- "CA"

all <- rbind(sl, ca)

library(dplyr); library(ggplot2)

per_change <- function(old, new) (new - old)/old * 100
per_reduction <- function(old, new) -per_change(old, new)

p <- group_by(all, Location, Data) %>%
  summarize(mse = min(mse)) %>% group_by(Location) %>% 
  mutate(PercentReduction = per_reduction(max(mse), mse)) %>%
  # Because the EVI Lag is the max mse, we can drop it: 
  filter(Data != "EVI Lag") %>%
  ggplot(aes(Location, PercentReduction, fill = Data)) +
  ylab("% Reduction in MSE from MSE of EVI Lag Univariate Model in Location") +
  geom_bar(stat = "identity", position = "dodge") + 
  theme_classic() +
  scale_fill_brewer(palette = "Dark2") +
  theme(legend.position=c(0.2, 0.9))

pdf(paste0("output/paper_plots/model_selection.pdf"), 
    width=5, height=6)
print(p)
dev.off()

jpeg(paste0("output/paper_plots/model_selection.jpg"), 
     width=5, height=6, units = "in", res=300)
print(p)
dev.off() 