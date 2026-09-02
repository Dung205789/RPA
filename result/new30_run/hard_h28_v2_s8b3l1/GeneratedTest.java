import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[5]")).click();

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(230)"));
        actions.doubleClick(object1).perform();

        actions.sendKeys("Start").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object2 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(231)"));
        object2.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object3 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(231)"));
        actions.doubleClick(object3).perform();

        actions.sendKeys("Wait one minute").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[9]")).click();

        WebElement object4 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(233)"));
        object4.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object5 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(233)"));
        actions.doubleClick(object5).perform();

        actions.sendKeys("Water boiled ?").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[9]")).click();

        WebElement object6 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(233)"));
        object6.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object7 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(233)"));
        object7.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object8 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(233)"));
        object8.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object9 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(233)"));
        actions.doubleClick(object9).perform();

        actions.sendKeys("Strong enough ?").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[9]")).click();

        WebElement object14 = driver.findElement(By.xpath("//not-found"));
        object14.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object19 = driver.findElement(By.xpath("//not-found"));
        object19.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object24 = driver.findElement(By.xpath("//not-found"));
        object24.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object29 = driver.findElement(By.xpath("//not-found"));
        object29.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object30 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(233)"));
        actions.doubleClick(object30).perform();

        actions.sendKeys("Milk wanted ?").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object35 = driver.findElement(By.xpath("//not-found"));
        object35.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object40 = driver.findElement(By.xpath("//not-found"));
        object40.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object45 = driver.findElement(By.xpath("//not-found"));
        object45.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object46 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(235)"));
        actions.doubleClick(object46).perform();

        actions.sendKeys("Fill the kettle").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object51 = driver.findElement(By.xpath("//not-found"));
        object51.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object52 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(235)"));
        actions.doubleClick(object52).perform();

        actions.sendKeys("Switch it on").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[5]")).click();

        WebElement object57 = driver.findElement(By.xpath("//not-found"));
        object57.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object62 = driver.findElement(By.xpath("//not-found"));
        object62.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object67 = driver.findElement(By.xpath("//not-found"));
        object67.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object68 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(235)"));
        actions.doubleClick(object68).perform();

        actions.sendKeys("Tea is ready").perform();

        WebElement object69 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(230)"));
        WebElement relatedObject1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(231)"));
        actions.moveToElement(object69, 0, object69.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object70 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(233)"));
        WebElement relatedObject2 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object70, 0, object70.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject2, 0, -relatedObject2.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object71 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject3 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(233)"));
        actions.moveToElement(object71, 0, object71.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject3, 0, -relatedObject3.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object76 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object76).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Not yet");

        WebElement object77 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject4 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object77, 0, object77.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject4, 0, -relatedObject4.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object82 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object82).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Yes");

        WebElement object83 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject5 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(235)"));
        actions.moveToElement(object83, 0, object83.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject5, 0, -relatedObject5.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object88 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object88).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Yes");

        WebElement object89 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject6 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object89, 0, object89.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject6, 0, -relatedObject6.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object94 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object94).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("No");

        WebElement object95 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(235)"));
        WebElement relatedObject7 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object95, 0, object95.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject7, 0, -relatedObject7.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object100 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object100).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Yes");

        WebElement object101 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(235)"));
        WebElement relatedObject8 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object101, 0, object101.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject8, 0, -relatedObject8.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object106 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object106).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("No");

        WebElement object107 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject9 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object107, 0, object107.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject9, 0, -relatedObject9.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object108 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject10 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object108, 0, object108.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject10, 0, -relatedObject10.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.quit();
    }
}