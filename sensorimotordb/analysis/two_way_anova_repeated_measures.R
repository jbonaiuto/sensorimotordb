two_way_anova_repeated_measures<-function(data, subject_var, resp_var, factor1, factor2){

    # Make sure needed packages are installed and loaded
    if(length(new<-(packages<-c("lsmeans","lme4","afex"))[!(packages %in% installed.packages()[,"Package"])])){
        install.packages(new[!(new %in% installed.packages()[,"Package"])])
    }
    sapply(packages, require, character.only=T)
    data[,subject_var]=factor(data[,subject_var])

    # Construct ANOVA formula
    f <- paste(resp_var, "~", factor1, "*", factor2, "+ Error(",subject_var,")")

    # Run ANOVA and get results
    anova_results=do.call("aov", list(as.formula(f), data=data))

    f <- paste(resp_var, "~", factor1, "*", factor2, "+ (1|",subject_var,")")
    model<-do.call("lmer", list(as.formula(f), data=data))

    f <- paste("pairwise ~", factor1, "*", factor2)
    twoway_pairwise<-do.call("lsmeans", list(model, as.formula(f)))

    f <- paste("pairwise ~", factor1)
    factor1_pairwise<-do.call("lsmeans", list(model, as.formula(f)))

    f <- paste("pairwise ~", factor2)
    factor2_pairwise<-do.call("lsmeans", list(model, as.formula(f)))

    # Return results as a list
    x<-summary(anova_results)
    #result <- list("anova"=summary(anova_results), "pairwise"=summary(pairwise$contrasts))
    result <- list("anova_trial"=x$'Error: trial', "anova_within"=x$'Error: Within', "twoway_pairwise"=summary(twoway_pairwise)$contrasts, "factor1_pairwise"=summary(factor1_pairwise)$contrasts, "factor2_pairwise"=summary(factor2_pairwise)$contrasts)
    return(result)
}