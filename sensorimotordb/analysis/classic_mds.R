classic_mds<-function(data, num_dims){

    d <- dist(na.omit(data)) # euclidean distances between the rows
    fit <- cmdscale(na.omit(d),eig=TRUE, k=num_dims) # k is the number of dim

    return(fit$points)
}