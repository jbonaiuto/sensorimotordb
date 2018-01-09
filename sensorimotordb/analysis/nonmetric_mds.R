nonmetric_mds<-function(data, num_dims){

    # Make sure needed packages are installed and loaded
    if(length(new<-(packages<-c("MASS"))[!(packages %in% installed.packages()[,"Package"])])){
        install.packages(new[!(new %in% installed.packages()[,"Package"])])
    }
    sapply(packages, require, character.only=T)

    d <- dist(na.omit(data)) # euclidean distances between the rows
    d <- d+0.0001
    fit <- isoMDS(na.omit(d), k=num_dims)

    return(fit$points)
}