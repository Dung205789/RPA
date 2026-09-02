import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(190)"));
        actions.doubleClick(object1).perform();

        actions.sendKeys("Lamp does not work").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object2 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(191)"));
        object2.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object3 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(191)"));
        actions.doubleClick(object3).perform();

        actions.sendKeys("Check the socket").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[9]")).click();

        WebElement object8 = driver.findElement(By.xpath("//not-found"));
        object8.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object9 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(192)"));
        actions.doubleClick(object9).perform();

        actions.sendKeys("Plugged in ?").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object14 = driver.findElement(By.xpath("//not-found"));
        object14.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object19 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object19).perform();

        actions.sendKeys("Plug it in").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object24 = driver.findElement(By.xpath("//not-found"));
        object24.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object29 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object29).perform();

        actions.sendKeys("Replace the bulb").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object34 = driver.findElement(By.xpath("//not-found"));
        object34.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object39 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object39).perform();

        actions.sendKeys("Lamp works").perform();

        WebElement object40 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(190)"));
        WebElement relatedObject1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(191)"));
        actions.moveToElement(object40, 0, object40.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object41 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(191)"));
        WebElement relatedObject2 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(192)"));
        actions.moveToElement(object41, 0, object41.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject2, 0, -relatedObject2.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object42 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(192)"));
        WebElement relatedObject3 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(192)"));
        actions.moveToElement(object42, 0, object42.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject3, 0, -relatedObject3.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object47 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object47).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("No");

        WebElement object48 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(192)"));
        WebElement relatedObject4 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object48, 0, object48.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject4, 0, -relatedObject4.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object53 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object53).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Yes");

        WebElement object54 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject5 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object54, 0, object54.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject5, 0, -relatedObject5.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object55 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject6 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object55, 0, object55.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject6, 0, -relatedObject6.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.quit();
    }
}