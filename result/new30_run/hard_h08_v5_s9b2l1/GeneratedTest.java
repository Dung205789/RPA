import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[5]")).click();

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(184)"));
        actions.doubleClick(object1).perform();

        actions.sendKeys("Model loaded").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[9]")).click();

        WebElement object6 = driver.findElement(By.xpath("//not-found"));
        object6.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object7 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(186)"));
        actions.doubleClick(object7).perform();

        actions.sendKeys("Bed level ?").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object12 = driver.findElement(By.xpath("//not-found"));
        object12.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object17 = driver.findElement(By.xpath("//not-found"));
        object17.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object22 = driver.findElement(By.xpath("//not-found"));
        object22.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object23 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(186)"));
        actions.doubleClick(object23).perform();

        actions.sendKeys("Slice the model").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object28 = driver.findElement(By.xpath("//not-found"));
        object28.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object33 = driver.findElement(By.xpath("//not-found"));
        object33.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object38 = driver.findElement(By.xpath("//not-found"));
        object38.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object43 = driver.findElement(By.xpath("//not-found"));
        object43.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object48 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object48).perform();

        actions.sendKeys("Heat the nozzle").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object53 = driver.findElement(By.xpath("//not-found"));
        object53.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object58 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object58).perform();

        actions.sendKeys("Level the bed").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object63 = driver.findElement(By.xpath("//not-found"));
        object63.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object68 = driver.findElement(By.xpath("//not-found"));
        object68.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object73 = driver.findElement(By.xpath("//not-found"));
        object73.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object78 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object78).perform();

        actions.sendKeys("Adjust the screws").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object83 = driver.findElement(By.xpath("//not-found"));
        object83.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object88 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object88).perform();

        actions.sendKeys("Clean the plate").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object93 = driver.findElement(By.xpath("//not-found"));
        object93.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object98 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object98).perform();

        actions.sendKeys("First layer stuck ?").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object103 = driver.findElement(By.xpath("//not-found"));
        object103.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object108 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object108).perform();

        actions.sendKeys("Part finished").perform();

        WebElement object109 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(184)"));
        WebElement relatedObject1 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object109, 0, object109.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object110 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject2 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(186)"));
        actions.moveToElement(object110, 0, object110.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject2, 0, -relatedObject2.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object115 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object115).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Level");

        WebElement object116 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject3 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object116, 0, object116.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject3, 0, -relatedObject3.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object121 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object121).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Off");

        WebElement object122 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject4 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object122, 0, object122.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject4, 0, -relatedObject4.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object123 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(186)"));
        WebElement relatedObject5 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object123, 0, object123.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject5, 0, -relatedObject5.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object124 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject6 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object124, 0, object124.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject6, 0, -relatedObject6.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object125 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject7 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object125, 0, object125.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject7, 0, -relatedObject7.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object126 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject8 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object126, 0, object126.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject8, 0, -relatedObject8.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object127 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject9 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object127, 0, object127.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject9, 0, -relatedObject9.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object132 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object132).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Peeling");

        WebElement object133 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject10 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object133, 0, object133.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject10, 0, -relatedObject10.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object138 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object138).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Stuck");

        driver.quit();
    }
}