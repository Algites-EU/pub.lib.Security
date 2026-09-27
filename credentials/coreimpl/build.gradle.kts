plugins {
    `java-library`
    `maven-publish`
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(17))
    }
    sourceSets {
        val main by getting {
            java.setSrcDirs(listOf("src/product/java"))
            resources.setSrcDirs(listOf("src/product/resources"))
        }
        val test by getting {
            java.setSrcDirs(listOf("src/develop/java"))
            resources.setSrcDirs(listOf("src/develop/resources"))
        }
    }
}

dependencies {
    api(project(":credentials:coreintf"))
    implementation("com.fasterxml.jackson.core:jackson-databind:2.18.2")
    implementation("com.fasterxml.jackson.dataformat:jackson-dataformat-yaml:2.18.2")

    runtimeOnly(project(":credentials:winstore"))
    runtimeOnly(project(":credentials:macstore"))
    runtimeOnly(project(":credentials:secretservicestore"))

    testImplementation("org.testng:testng:7.11.0")
}
