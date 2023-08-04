# Note: First set working directory to labc-study

rm(list=ls())
set.seed(100)

library(dplyr)
library(lfe)
library(stargazer)
library(survival)
library(survminer)
library(data.table)

df <- read.csv("intermediate/data_main.csv")

#-------------------- VARIABLE DEFINITIONS

df$UNITS100 <- df$DU_CHANGED/100                   # units per 100
df$HEIGHT10 <- df$HEIGHT/10                        # height per 10 ft
df$SQFT10K <- df$SQUARE_FOOTAGE/10000              # sqft per 10k
df$AFFORDABLE <- ifelse(df$AFFORDABLE, 1, 0)       # 100% affordable project
df$MIXEDINCOME <- ifelse(df$MIXEDINCOME, 1, 0)     # mixed income project

df$BY_RIGHT <- (df$N_CASES==0)
df$CT <- df$CENSORED_TIME - df$APPROVAL_TIME
df$AT <- df$APPROVAL_TIME
df$APPROVED <- 1

oldnames = c("pfx_CPC", "sfx_CE", "sfx_MND", "sfx_EIR", "sfx_SPR", "sfx_SPP",
             "sfx_ZAA", "sfx_ZV", "sfx_CPIOC", "sfx_OVR", "sfx_DB",
             "POWER_OH", "POWER_UG")
newnames = c("CPC", "CE", "MND", "EIR", "SPR", "SPP",
             "ZAA", "ZV", "CPIOC", "OVR", "DB",
             "POWER_OH", "POWER_UG")
setnames(df, old=oldnames, new=newnames)


#------------------- HELPER FUNCTIONS

build_formula <- function(yvar, covars) {
  fmla <- paste0(yvar, " ~ ", covars[1])
  for (covar in covars[2:length(covars)]) {
    fmla <- paste0(fmla, " + ", covar)
  }
  return(as.formula(fmla))
}

simulateCT <- function(newdata, reg) {
  newdata$xbetaC <- predict(reg, newdata=newdata)
  for (i in 1:nrow(newdata)) {
    if (newdata[i, "IS_COMPLETE"]==1) {
      newdata[i, "epsC"] = newdata[i, "CT"] - newdata[i, "xbetaC"]
    }
    else {
      eps_min = newdata[i, "CT"] - newdata[i, "xbetaC"]
      newdata[i, "epsC_min"] = eps_min
      r = rlogis(n=1, location=0, scale=reg$scale)
      while (r < eps_min) {
        r = rlogis(n=1, location=0, scale=reg$scale)
      }
      newdata[i, "epsC"] = r
    }
    newdata[i, "epsC_quantile"] = 1/(1+exp(-newdata[i,"epsC"]/reg$scale))
  }
  return(newdata)
}


#-------------------- BASIC SIMULATION

r0 <- survreg(build_formula(
  "Surv(CT,IS_COMPLETE)", c("UNITS100","HEIGHT10","SQFT10K")),
  data=df, dist="logistic")

newdata <- df
newdata <- simulateCT(newdata, r0)
newdata$SIMULATED_APPROVAL_TIME <- 0.75*newdata$APPROVAL_TIME
newdata$SIMULATED_TOTAL_TIME <- newdata$SIMULATED_APPROVAL_TIME + newdata$xbetaC + newdata$epsC

write.csv(select(newdata, PERMIT_NBR, SIMULATED_TOTAL_TIME), "intermediate/data_basic_sim.csv", row.names=F)


#-------------------- DETAILED REGRESSIONS

set.seed(100)

covars1 <- c("UNITS100", "HEIGHT10", "SQFT10K", "AFFORDABLE", "MIXEDINCOME", "BY_RIGHT")
covars2 <- newnames
covars3 <- c("as.factor(CD)")

r2 <- survreg(build_formula(
  "Surv(AT,APPROVED)", c(covars1, covars2, covars3)
), data=df, dist="logistic")

r4 <- survreg(build_formula(
  "Surv(CT,IS_COMPLETE)", c(covars1, covars2, covars3)
), data=df, dist="logistic")

stargazer(
  r2,r4,type="latex",
  keep=c(covars1,covars2,"Constant"), 
  add.lines=list(c("Council District FE", "N", "Y", "N", "Y")),
  no.space=T
)

coef_df = data.frame(
  variable = names(r2$coefficients),
  coef_r2 = r2$coefficients, 
  coef_r4 = r4$coefficients
)
coef_df$effect <- coef_df$coef_r2 + coef_df$coef_r4

write.csv(coef_df, "intermediate/coefs.csv", row.names=F)


#-------------------------- DETAILED SIMULATIONS

newdata <- df
newdata$xbetaA <- predict(r2, newdata=newdata)
newdata$epsA <- newdata$AT - newdata$xbetaA
newdata <- simulateCT(newdata, r4)

write.csv(
  select(newdata, PERMIT_NBR, xbetaA, epsA, xbetaC, epsC, epsC_quantile, epsC_min), 
  "intermediate/data_detailed_sim.csv", 
  row.names=F
)

