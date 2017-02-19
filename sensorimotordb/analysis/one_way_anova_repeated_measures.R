one_way_anova_repeated_measures<-function(data, subject_var, resp_var, factor1){

    data[,subject_var]=factor(data[,subject_var])

    # Construct ANOVA formula
    f <- paste(resp_var, "~", factor1,"+Error(",subject_var,")")

    # Run ANOVA and get results
    anova_results=do.call("aov", list(as.formula(f), data=data))


    # Get pairwise comparisons
    factor1_pairwise=pairwise.t.test(x=data[,resp_var], g=data[,factor1], p.adjust.method="bonf", paired=T)

    # Return results as a list
    result <- list("anova"=summary(anova_results), "factor1_pairwise"=factor1_pairwise$p.value)
    return(result)
}