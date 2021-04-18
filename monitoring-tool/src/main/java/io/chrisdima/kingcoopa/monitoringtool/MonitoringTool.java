package io.chrisdima.kingcoopa.monitoringtool;

import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.Map;

public class MonitoringTool {
  public MonitoringTool() {}

  public static String getInfo() throws IOException {
    StringBuilder builder = new StringBuilder();
    try (BufferedReader reader = new BufferedReader(
        new InputStreamReader(new URL("http://192.168.1.9:8080/info").openStream()))) {
      for (String line; (line = reader.readLine()) != null;) {
        builder.append(line);
      }
    }

    return builder.toString();
  }

  public static void main(String[] args) {
    try {
//      getInfo();
        /* Amazon S3: */
         MinioClient minioClient =
             MinioClient.builder()
                 .endpoint("https://s3.amazonaws.com")
                 .credentials(
                     System.getenv("AWS_ACCESS_KEY"), System.getenv("AWS_SECRET_KEY"))
                 .build();

        ByteArrayInputStream bais = new ByteArrayInputStream(
            getInfo().getBytes("UTF-8"));

        minioClient.putObject(
            PutObjectArgs
                .builder()
                .bucket("king-coopa")
                .object("info.json")
                .contentType("application/json")
                .userMetadata(Map.of("x-amz-acl", "public-read"))
                .stream(bais, bais.available(), -1).build());
        bais.close();
        System.out.println("my-objectname is uploaded successfully");

      } catch (Exception e) {
        System.out.println("Error occurred: " + e);
      }
    }
}
