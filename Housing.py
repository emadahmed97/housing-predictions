import findspark
from pyspark.sql import SparkSession
from pyspark.ml.regression import LinearRegression
from pyspark.sql import Row
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.ml.linalg import DenseVector
from pyspark.ml.feature import StandardScaler

x = findspark.find()
print(x)
findspark.init("C:/spark/spark-2.3.0-bin-hadoop2.7")
spark = SparkSession.builder.master("local").appName("Linear Regression Model").config("spark.executor.memory", "1gb").getOrCreate()
sc = spark.sparkContext

rdd = sc.textFile('C:/Users/Emad Ahmed/Desktop/CaliforniaHousing/cal_housing.data')
header = sc.textFile('C:/Users/Emad Ahmed/Desktop/CaliforniaHousing/cal_housing.domain')
header.collect()

rdd = rdd.map(lambda line: line.split(","))

# RDD -> DF
df = rdd.map(lambda line: Row(longitude=line[0], 
                              latitude=line[1], 
                              housingMedianAge=line[2],
                              totalRooms=line[3],
                              totalBedRooms=line[4],
                              population=line[5], 
                              households=line[6],
                              medianIncome=line[7],
                              medianHouseValue=line[8])).toDF()
#df.show()

#df.printSchema()

def convertColumn(df, names, newType):
  for name in names: 
     df = df.withColumn(name, df[name].cast(newType))
  return df 

# Assign all column names to `columns`
columns = ['households', 'housingMedianAge', 'latitude', 'longitude', 'medianHouseValue', 'medianIncome', 'population', 'totalBedRooms', 'totalRooms']

# Conver the `df` columns to `FloatType()`
df = convertColumn(df, columns, FloatType())

df.select('population','totalBedRooms').show(10)

df.groupBy("housingMedianAge").count().sort("housingMedianAge",ascending=False).show()

#df.describe().show()

df = df.withColumn("medianHouseValue", col("medianHouseValue")/100000)

#df.take(2)

#TRANSFORMATION

roomsPerHousehold = df.select(col("totalRooms")/col("households"))

populationPerHousehold = df.select(col("population")/col("households"))

bedroomsPerRoom = df.select(col("totalBedRooms")/col("totalRooms"))


df = df.withColumn("roomsPerHousehold", col("totalRooms")/col("households"))    .withColumn("populationPerHousehold", col("population")/col("households"))    .withColumn("bedroomsPerRoom", col("totalBedRooms")/col("totalRooms"))

#df.first()

df = df.select("medianHouseValue", 
              "totalBedRooms", 
              "population", 
              "households", 
              "medianIncome", 
              "roomsPerHousehold", 
              "populationPerHousehold", 
              "bedroomsPerRoom")

input_data = df.rdd.map(lambda x: (x[0], DenseVector(x[1:])))

df = spark.createDataFrame(input_data, ["label", "features"])

standardScaler = StandardScaler(inputCol="features", outputCol="features_scaled")

scaler = standardScaler.fit(df)

scaled_df = scaler.transform(df)

#scaled_df.take(2)

# PREDICTION
train_data, test_data = scaled_df.randomSplit([.8,.2],seed=1234)

lr = LinearRegression(labelCol="label", maxIter=10, regParam=0.3, elasticNetParam=0.8)

linearModel = lr.fit(train_data)

predicted = linearModel.transform(test_data)

predictions = predicted.select("prediction").rdd.map(lambda x: x[0])
labels = predicted.select("label").rdd.map(lambda x: x[0])

predictionAndLabel = predictions.zip(labels).collect()

predictionAndLabel[:5]

linearModel.coefficients
linearModel.intercept

linearModel.summary.rootMeanSquaredError

linearModel.summary.r2

spark.stop()