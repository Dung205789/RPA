import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[1]")).click();

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(195)"));
        actions.doubleClick(object1).perform();

        actions.sendKeys("Start").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[9]")).click();

        WebElement object2 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(196)"));
        object2.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object3 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(196)"));
        actions.doubleClick(object3).perform();

        actions.sendKeys("Water boiled ?").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object8 = driver.findElement(By.xpath("//not-found"));
        object8.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object13 = driver.findElement(By.xpath("//not-found"));
        object13.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object18 = driver.findElement(By.xpath("//not-found"));
        object18.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object19 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(198)"));
        actions.doubleClick(object19).perform();

        actions.sendKeys("Fill the kettle").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object24 = driver.findElement(By.xpath("//not-found"));
        object24.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object29 = driver.findElement(By.xpath("//not-found"));
        object29.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object34 = driver.findElement(By.xpath("//not-found"));
        object34.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object39 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object39).perform();

        actions.sendKeys("Strong enough ?").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object44 = driver.findElement(By.xpath("//not-found"));
        object44.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object49 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object49).perform();

        actions.sendKeys("Wait one minute").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object54 = driver.findElement(By.xpath("//not-found"));
        object54.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object59 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object59).perform();

        actions.sendKeys("Tea is ready").perform();

        WebElement object60 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(195)"));
        WebElement relatedObject1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(196)"));
        actions.moveToElement(object60, 0, object60.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object61 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(196)"));
        WebElement relatedObject2 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(198)"));
        actions.moveToElement(object61, 0, object61.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject2, 0, -relatedObject2.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object62 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(198)"));
        actions.doubleClick(object62).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Yes");

        WebElement object63 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(199)"));
        WebElement relatedObject3 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object63, 0, object63.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject3, 0, -relatedObject3.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object68 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object68).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Not yet");

        WebElement object69 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(200)"));
        WebElement relatedObject4 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object69, 0, object69.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject4, 0, -relatedObject4.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object70 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject5 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object70, 0, object70.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject5, 0, -relatedObject5.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object75 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object75).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("No");

        WebElement object76 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject6 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object76, 0, object76.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject6, 0, -relatedObject6.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object77 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject7 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object77, 0, object77.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject7, 0, -relatedObject7.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object82 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object82).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Yes");

        WebElement object83 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject8 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object83, 0, object83.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject8, 0, -relatedObject8.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.quit();
    }
}