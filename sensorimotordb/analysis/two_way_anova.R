two_way_anova<-function(data, resp_var, factor1, factor2){

    # Make sure needed packages are installed and loaded
    if(length(new<-(packages<-c("Rmisc","lsmeans"))[!(packages %in% installed.packages()[,"Package"])])){
        install.packages(new[!(new %in% installed.packages()[,"Package"])])
    }
    sapply(packages, require, character.only=T)

    # Construct ANOVA formula
    f <- paste(resp_var, "~", factor1, " + ", factor2, " + ", factor1, ":", factor2)

    # Run ANOVA and get results
    model=do.call("lm", list(as.formula(f), data=data))
    anova_results<-anova(model)

    # Get pairwise comparisons
    f <- paste("pairwise~", factor1, "*", factor2, "|", factor1)
    factor1_pairwise=do.call("lsmeans", list(model, as.formula(f)))
    f <- paste("pairwise~", factor1, "*", factor2, "|", factor2)
    factor2_pairwise=do.call("lsmeans", list(model, as.formula(f)))

    # Return results as a list
    result <- list("anova"=anova_results, "factor1_pairwise"=summary(factor1_pairwise)$contrasts, "factor2_pairwise"=summary(factor2_pairwise)$contrasts)
    return(result)
}