kmeans_clustering<-function(data, num_clusters){

    clusters <- kmeans(na.omit(data), num_clusters)

    return(clusters)
}