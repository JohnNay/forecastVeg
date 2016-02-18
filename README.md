<!-- README.md is generated from README.Rmd. Please edit that file -->
Forecasting Vegetation Health at High Spatial Resolution
========================================================

Drought threatens food and water security around the world, and this threat is likely to become more severe under climate change. High resolution predictive information can help farmers, water managers, and others to manage the effects of drought. We have created a tool to produce short-term forecasts of vegetation health at high spatial resolution, using open source software and [NASA satellite data](http://modis.gsfc.nasa.gov/data/dataprod/index.php) that are global in coverage. The tool automates downloading and processing Moderate Resolution Imaging Spectroradiometer (MODIS) datasets, and training gradient-boosted machine models on hundreds of millions of observations to predict future values of the Enhanced Vegetation Index. We compared the predictive power of different sets of variables (raw spectral MODIS data and Level-3 MODIS products) in two regions with distinct agro-ecological systems, climates, and cloud coverage: Sri Lanka and California. Our tool provides considerably greater predictive power on held-out datasets than simpler baseline models.

This website hosts the supplementary material for this project by John J. Nay, Emily Burchfield, and Jonathan Gilligan, listing the external software requirements and the exact commands to be run in a terminal for completing our process.

The data downloading and processing requires a computer with significant amounts of RAM (\> 100 GB) because the data must be held in memory to manipulate it. The modeling and hyper-parameters search can be run on weaker machines but the training time will take months if run on a laptop. To complete model training and hyper-parameters search in a few days, train the models on a computer with \>= available 32 threads and \>= 100 GB RAM.

If you use these scripts, cite this paper:

Nay, John J., Burchfield, Emily, Gilligan, Jonathan. (2016) Forecasting Vegetation Health at High Spatial Resolution.

United States National Science Foundation grant EAR-1204685 funded this research.

Requirements
============

-   Python 2.7 <https://www.python.org/download/releases/2.7/>
-   h2o 3 <http://www.h2o.ai/download/h2o/python>

<!-- -->

    [sudo] pip install requests # for h2o
    [sudo] pip install tabulate # for h2o
    [sudo] pip install numpy # for reshaping and saving data
    [sudo] pip install pandas # for reshaping and saving data
    [sudo] pip install hyperopt # for estimating hyper-parameters of h2o models
    [sudo] pip install annoy # for baseline model

The optional visualizations of validation performance requires R, and the R packages dplyr, ggplot2, and ggExtra.

Overview:
=========

![Methods Diagram](figures/methods_diagram.jpg)

Data construction:
==================

python -u 0\_matrix\_construction.py spectral directory username password tiles today enddate referenceImage \> 0\_construct.log &

-   python -u 0\_matrix\_construction.py 1 /data/emily/SL myusername mypassword 'h25v08 h26v08' 2014-01-30 2014-01-01 /data/emily/WF/NDVI\_DC/SL.tif

Pre-processing (spectral and non-spectral use different scripts):
=================================================================

### For non-spectral:

python -u 1\_pre\_process.py *load\_data\_fp save\_data\_fp load\_extra\_file* \> 1\_process.log &

-   load\_extra\_file is optional, its used when an analyst has ancillary data, e.g. land-use classifications
-   python -u 1\_pre\_process.py /data/emily/SL/ /data/john/srilanka/data1.csv /data/NDVI/columns/landuse.npy \> 1\_process.log &
-   python -u 1\_pre\_process.py /data/emily/CA/ /data/john/CA/data1.csv /data/emily/SJ/SJlanduse.npy \> 1\_processCA.log &

### For spectral:

python -u 1\_pre\_processS.py *load\_data\_fp save\_data\_fp old\_data\_fp load\_extra\_file* \> 1\_processS.log &

-   python -u 1\_pre\_processS.py /data/emily/SLs/ /data/john/srilanka/data1S.csv /data/john/srilanka/data1.csv /data/NDVI/columns/landuse.npy \> 1\_processS.log &
    -   python -u 1\_pre\_processS.py /data/emily/CAs/ /data/john/CA/data1S.csv /data/john/CA/data1.csv /data/emily/SJ/SJlanduse.npy \> 1\_processSCA.log &

For h2o:
--------

### For non-spectral:

python -u 2\_h2o\_process.py *load\_data\_fp save\_data\_fp* \> 2a\_h2o.log &

-   python -u 2\_h2o\_process.py /data/john/srilanka/data1.csv /data/john/srilanka/h2o\_data\_withMissing \> 2a\_h2o.log &
-   python -u 2\_h2o\_process.py /data/john/CA/data1.csv /data/john/CA/h2o\_data\_withMissing \> 2a\_h2oCA.log &

python -u 2\_h2o\_process\_2.py *load\_data\_fp save\_training\_data\_fp save\_holdout\_data\_fp save\_training\_ind\_fp* \> 2b\_h2o.log &

*save\_training\_ind\_fp* is an optional argument for the 2\_h2o\_process\_2.py script. If it is provided, then the script will create a column indicating whether each row is in the training or testing data. This column will be used by subsequent scripts in dividing data into training and testing (not hold-out data, that was done previously). When we run the spectral we usually do not specify this argument because we don't want to overwite the file we created for the level-3 data: this allows us to use the same training/test split and compare performance across predictor variable data type.

-   python -u 2\_h2o\_process\_2.py /data/john/srilanka/h2o\_data\_withMissing /data/john/srilanka/h2o\_data\_training /data/john/srilanka/h2o\_data\_holdout /data/john/srilanka/random\_split\_for\_training.csv \> 2b\_h2o.log &
-   python -u 2\_h2o\_process\_2.py /data/john/CA/h2o\_data\_withMissing /data/john/CA/h2o\_data\_training /data/john/CA/h2o\_data\_holdout /data/john/CA/random\_split\_for\_training.csv \> 2b\_h2oCA.log &

### For spectral:

python -u 2\_h2o\_processS.py *load\_data\_fp save\_data\_fp* \> 2a\_h2oS.log &

-   python -u 2\_h2o\_processS.py /data/john/srilanka/data1S.csv /data/john/srilanka/h2o\_data\_withMissingS \> 2a\_h2oS.log &
-   python -u 2\_h2o\_processS.py /data/john/CA/data1S.csv /data/john/CA/h2o\_data\_withMissingS \> 2a\_h2oSCA.log &

python -u 2\_h2o\_process\_2.py *load\_data\_fp save\_training\_data\_fp save\_holdout\_data\_fp* \> 2b\_h2oS.log &

-   Starting here, all the scripts are the same for spectral and non spectral. You just pass them different arguments.
-   If you run non-spectral first, you can not specify the *save\_training\_ind\_fp* with 2\_h2o\_process\_2.py and thus not over-wrtie the csv file with the vector of indices denoting a training and testing data split. This allows results to be comparable between spectral and non-spectral.
-   python -u 2\_h2o\_process\_2.py /data/john/srilanka/h2o\_data\_withMissingS /data/john/srilanka/h2o\_data\_trainingS /data/john/srilanka/h2o\_data\_holdoutS \> 2b\_h2oS.log &
-   python -u 2\_h2o\_process\_2.py /data/john/CA/h2o\_data\_withMissingS /data/john/CA/h2o\_data\_trainingS /data/john/CA/h2o\_data\_holdoutS \> 2b\_h2oSCA.log &

For baseline:
-------------

python -u 2\_baseline\_process.py load\_data\_fp save\_data\_fp \> 2\_baseline.log &

-   python -u 2\_baseline\_process.py /data/john/srilanka/data1.csv /data/john/srilanka/baseline\_data.csv \> 2\_baseline.log &
-   python -u 2\_baseline\_process.py /data/john/CA/data1.csv /data/john/CA/baseline\_data.csv \> 2\_baselineCA.log &

Modeling (spectral and non-spectral use same scripts, just different arguments for predictor variables)
=======================================================================================================

Modeling in h2o with GBM:
=========================

For non-spectral:
-----------------

python -u 3\_h2o\_gbm.py *load\_data\_fp* *load\_train\_ind\_fp* *saving\_fp* GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_gbm.log &

-   python -u 3\_h2o\_gbm.py /data/john/srilanka/h2o\_data\_training /data/john/srilanka/random\_split\_for\_training.csv output/gbmres.csv GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_gbm.log &
    -   python -u 3\_h2o\_gbm.py /data/john/srilanka/h2o\_data\_training /data/john/srilanka/random\_split\_for\_training.csv output/gbmres\_evi.csv EVI\_lag \> 3\_gbmevi.log &
    -   python -u 3\_h2o\_gbm.py /data/john/srilanka/h2o\_data\_training /data/john/srilanka/random\_split\_for\_training.csv output/gbmres\_evilt.csv time\_period EVI\_lag landuse \> 3\_gbmevilt.log &
-   python -u 3\_h2o\_gbm.py /data/john/CA/h2o\_data\_training /data/john/CA/random\_split\_for\_training.csv output/gbmresCA.csv GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_gbmCA.log &
    -   python -u 3\_h2o\_gbm.py /data/john/CA/h2o\_data\_training /data/john/CA/random\_split\_for\_training.csv output/gbmresCA\_evi.csv EVI\_lag \> 3\_gbmCAevi.log &
    -   python -u 3\_h2o\_gbm.py /data/john/CA/h2o\_data\_training /data/john/CA/random\_split\_for\_training.csv output/gbmresCA\_evilt.csv time\_period EVI\_lag landuse \> 3\_gbmCAevilt.log &

For spectral:
-------------

python -u 3\_h2o\_gbm.py *load\_data\_fp* *load\_train\_ind\_fp* *saving\_fp* B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_gbm.log &

-   python -u 3\_h2o\_gbm.py /data/john/srilanka/h2o\_data\_trainingS /data/john/srilanka/random\_split\_for\_training.csv output/gbmresS.csv B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_gbm.log &
-   python -u 3\_h2o\_gbm.py /data/john/CA/h2o\_data\_trainingS /data/john/CA/random\_split\_for\_training.csv output/gbmresSCA.csv B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_gbmCA.log &

Modeling in h2o with deep learning (both model-imputed and mean-imputed):
=========================================================================

For non-spectral:
-----------------

python -u 3\_h2o\_deeplearning\_imputation.py *load\_data\_fp saving\_meanImputed\_fp saving\_modelImputed\_fp saving\_means\_fp saving\_models\_fp* GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_imp.log &

-   python -u 3\_h2o\_deeplearning\_imputation.py /data/john/srilanka/h2o\_data\_training /data/john/srilanka/mean\_imputed\_data /data/john/srilanka/model\_imputed\_data /data/john/srilanka/dl\_imputation\_means.csv /data/john/srilanka/models/ GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_imp.log &
    -   python -u 3\_h2o\_deeplearning\_imputation.py /data/john/CA/h2o\_data\_training /data/john/CA/mean\_imputed\_data /data/john/CA/model\_imputed\_data /data/john/CA/dl\_imputation\_means.csv /data/john/CA/models/ GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_impCA.log &

python -u 3\_h2o\_deeplearning.py *load\_data\_fp load\_train\_ind\_fp saving\_fp* GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_mean.log &

-   python -u 3\_h2o\_deeplearning.py /data/john/srilanka/mean\_imputed\_data /data/john/srilanka/random\_split\_for\_training.csv output/dlres\_meanimputed.csv GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_mean.log &
    -   python -u 3\_h2o\_deeplearning.py /data/john/CA/mean\_imputed\_data /data/john/CA/random\_split\_for\_training.csv output/dlres\_meanimputedCA.csv GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_meanCA.log &
-   python -u 3\_h2o\_deeplearning.py /data/john/srilanka/model\_imputed\_data /data/john/srilanka/random\_split\_for\_training.csv output/dlres\_modelimputed.csv GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_model.log &
    -   python -u 3\_h2o\_deeplearning.py /data/john/CA/model\_imputed\_data /data/john/CA/random\_split\_for\_training.csv output/dlres\_modelimputedCA.csv GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_modelCA.log &

For spectral:
-------------

python -u 3\_h2o\_deeplearning\_imputation.py *load\_data\_fp saving\_meanImputed\_fp saving\_modelImputed\_fp saving\_means\_fp saving\_models\_fp* B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_imp.log &

-   python -u 3\_h2o\_deeplearning\_imputation.py /data/john/srilanka/h2o\_data\_trainingS /data/john/srilanka/mean\_imputed\_dataS /data/john/srilanka/model\_imputed\_dataS /data/john/srilanka/dl\_imputation\_meansS.csv /data/john/srilanka/modelsS/ B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_impS.log &
    -   python -u 3\_h2o\_deeplearning\_imputation.py /data/john/CA/h2o\_data\_trainingS /data/john/CA/mean\_imputed\_dataS /data/john/CA/model\_imputed\_dataS /data/john/CA/dl\_imputation\_meansS.csv /data/john/CA/modelsS/ B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_impSCA.log &

python -u 3\_h2o\_deeplearning.py *load\_data\_fp load\_train\_ind\_fp saving\_fp* B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_meanS.log &

-   python -u 3\_h2o\_deeplearning.py /data/john/srilanka/mean\_imputed\_dataS /data/john/srilanka/random\_split\_for\_training.csv output/dlres\_meanimputedS.csv B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_meanS.log &
    -   python -u 3\_h2o\_deeplearning.py /data/john/CA/mean\_imputed\_dataS /data/john/CA/random\_split\_for\_training.csv output/dlres\_meanimputedSCA.csv B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_meanSCA.log &
-   python -u 3\_h2o\_deeplearning.py /data/john/srilanka/model\_imputed\_dataS /data/john/srilanka/random\_split\_for\_training.csv output/dlres\_modelimputedS.csv B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_modelS.log &
    -   python -u 3\_h2o\_deeplearning.py /data/john/CA/model\_imputed\_dataS /data/john/CA/random\_split\_for\_training.csv output/dlres\_modelimputedSCA.csv B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 3\_dl\_modelSCA.log &

Predicting holdout:
===================

This data is reserved for final testing of the best model.

Only run the spectral or the level 3 (non-spectral) on the hold out data, not both. Choose the one that did the best on the test data in the previous scripts. Only run the deep learning or the GBM, not both. Choose the one that did the best on the test data in the previous scripts.

With Baseline:
--------------

python -u 4\_baseline.py *load\_data\_fp saving\_model saving\_fp saving\_predictions\_fp Trees Neighbs K* \> 4\_bline\_holdout.log &

-   python -u 4\_baseline.py /data/john/srilanka/baseline\_data.csv /data/john/srilanka/baseline\_model.ann output/baseline\_holdout.csv /data/john/srilanka/baseline\_predicted\_holdout.csv 7 30 10 \> 4\_bline\_holdout.log &
-   python -u 4\_baseline.py /data/john/CA/baseline\_data.csv /data/john/CA/baseline\_model.ann output/baseline\_holdout.csv /data/john/CA/baseline\_predicted\_holdout.csv 7 30 10 \> 4\_bline\_holdoutCA.log &

With Models:
------------

python -u 4\_holdout\_models.py *load\_data\_fp train\_data\_fp training\_res\_fp saving\_fp saving\_predictions\_fp saving\_varimp\_fp predictors* \> 4\_model\_holdout.log &

### For non-spectral and GBM:

-   python -u 4\_holdout\_models.py /data/john/srilanka/h2o\_data\_holdout /data/john/srilanka/h2o\_data\_training output/gbmres.csv output/gbm\_holdout\_final.csv /data/john/srilanka/gbm\_predicted\_holdout.csv output/gbm\_varimp.csv GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 4\_model\_holdout.log &
    -   python -u 4\_holdout\_models.py /data/john/CA/h2o\_data\_holdout /data/john/CA/h2o\_data\_training output/gbmresCA.csv output/gbm\_holdout\_finalCA.csv /data/john/CA/gbm\_predicted\_holdout.csv output/gbm\_varimpCA.csv GWP\_lag LST\_lag NDVI\_lag FPAR\_lag LAI\_lag GP\_lag PSN\_lag nino34\_lag time\_period EVI\_lag landuse \> 4\_model\_holdoutCA.log &

### For spectral and GBM:

-   python -u 4\_holdout\_models.py /data/john/srilanka/h2o\_data\_holdoutS /data/john/srilanka/h2o\_data\_trainingS output/gbmresS.csv output/gbm\_holdout\_finalS.csv /data/john/srilanka/gbm\_predicted\_holdoutS.csv output/gbm\_varimp.csv B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 4\_model\_holdoutS.log &
    -   python -u 4\_holdout\_models.py /data/john/CA/h2o\_data\_holdoutS /data/john/CA/h2o\_data\_trainingS output/gbmresSCA.csv output/gbm\_holdout\_finalSCA.csv /data/john/CA/gbm\_predicted\_holdoutS.csv output/gbm\_varimpCA.csv B1\_lag B2\_lag B3\_lag B4\_lag B5\_lag B6\_lag B7\_lag GWP\_lag nino34\_lag time\_period EVI\_lag landuse \> 4\_model\_holdoutSCA.log &

Create plots of validation performance:
=======================================

For model selection, the plot comparing the performance of the different data types and locations:

    Rscript paper_plots_modelSelection.R &

For final model validation on hold-out data, the many plots illustrating performance over space and time:

    Rscript paper_plots.R &
