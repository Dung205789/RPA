import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object5 = driver.findElement(By.xpath("//not-found"));
        object5.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        WebElement object10 = driver.findElement(By.xpath("//not-found"));
        object10.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        WebElement object15 = driver.findElement(By.xpath("//not-found"));
        object15.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        driver.findElement(By.xpath("//body/div[10]")).click();

        WebElement object20 = driver.findElement(By.xpath("//not-found"));
        object20.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        WebElement object25 = driver.findElement(By.xpath("//not-found"));
        object25.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        driver.findElement(By.xpath("//body/div[10]")).click();

        WebElement object30 = driver.findElement(By.xpath("//not-found"));
        object30.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }

        driver.findElement(By.xpath("//body/div[10]")).click();

        driver.findElement(By.xpath("//body/div[10]")).click();

        WebElement object35 = driver.findElement(By.xpath("//not-found"));
        object35.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object40 = driver.findElement(By.xpath("//not-found"));
        object40.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object45 = driver.findElement(By.xpath("//not-found"));
        object45.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object50 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object50).perform();

        actions.sendKeys("Start").perform();

        WebElement object55 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object55).perform();

        actions.sendKeys("Read A").perform();

        WebElement object60 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object60).perform();

        actions.sendKeys("Read B").perform();

        WebElement object65 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object65).perform();

        actions.sendKeys("Calculate Sum as A + B").perform();

        WebElement object70 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object70).perform();

        actions.sendKeys("Print Sum").perform();

        WebElement object75 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object75).perform();

        actions.sendKeys("End").perform();

        WebElement object76 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject1 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object76, 0, object76.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object77 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject2 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object77, 0, object77.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject2, 0, -relatedObject2.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object78 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject3 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object78, 0, object78.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject3, 0, -relatedObject3.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object79 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject4 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object79, 0, object79.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject4, 0, -relatedObject4.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object80 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject5 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object80, 0, object80.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject5, 0, -relatedObject5.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.findElement(By.xpath("//not-found")).click();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/a[63]/span[2]")).click();

        driver.findElement(By.xpath("//not-found")).click();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/a[14]/span[2]")).click();

        driver.findElement(By.xpath("//not-found")).click();

        driver.quit();
    }
}