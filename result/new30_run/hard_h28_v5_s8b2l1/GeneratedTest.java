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

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(244)"));
        actions.doubleClick(object1).perform();

        actions.sendKeys("Patch submitted").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[9]")).click();

        WebElement object2 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(245)"));
        object2.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object3 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(245)"));
        actions.doubleClick(object3).perform();

        actions.sendKeys("Tests pass ?").perform();

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
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object23 = driver.findElement(By.xpath("//not-found"));
        object23.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object24 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(247)"));
        actions.doubleClick(object24).perform();

        actions.sendKeys("Run the test suite").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object29 = driver.findElement(By.xpath("//not-found"));
        object29.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object34 = driver.findElement(By.xpath("//not-found"));
        object34.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object39 = driver.findElement(By.xpath("//not-found"));
        object39.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object44 = driver.findElement(By.xpath("//not-found"));
        object44.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object45 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(247)"));
        actions.doubleClick(object45).perform();

        actions.sendKeys("Fix the failing test").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object50 = driver.findElement(By.xpath("//not-found"));
        object50.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object51 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(248)"));
        actions.doubleClick(object51).perform();

        actions.sendKeys("Address the comments").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[9]")).click();

        WebElement object56 = driver.findElement(By.xpath("//not-found"));
        object56.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object57 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(248)"));
        actions.doubleClick(object57).perform();

        actions.sendKeys("Reviewer happy ?").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object62 = driver.findElement(By.xpath("//not-found"));
        object62.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object63 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(248)"));
        actions.doubleClick(object63).perform();

        actions.sendKeys("Assign a reviewer").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object68 = driver.findElement(By.xpath("//not-found"));
        object68.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object69 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(250)"));
        actions.doubleClick(object69).perform();

        actions.sendKeys("Patch merged").perform();

        WebElement object70 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(244)"));
        WebElement relatedObject1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(245)"));
        actions.moveToElement(object70, 0, object70.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object71 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(247)"));
        WebElement relatedObject2 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object71, 0, object71.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject2, 0, -relatedObject2.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object76 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object76).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Pass");

        WebElement object77 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject3 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(248)"));
        actions.moveToElement(object77, 0, object77.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject3, 0, -relatedObject3.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object78 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(247)"));
        WebElement relatedObject4 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(248)"));
        actions.moveToElement(object78, 0, object78.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject4, 0, -relatedObject4.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object79 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(248)"));
        actions.doubleClick(object79).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Fail");

        WebElement object80 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(251)"));
        WebElement relatedObject5 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object80, 0, object80.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject5, 0, -relatedObject5.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object81 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject6 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object81, 0, object81.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject6, 0, -relatedObject6.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object82 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject7 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(251)"));
        actions.moveToElement(object82, 0, object82.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject7, 0, -relatedObject7.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object87 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object87).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Changes needed");

        WebElement object88 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject8 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(253)"));
        actions.moveToElement(object88, 0, object88.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject8, 0, -relatedObject8.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object93 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object93).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Approved");

        WebElement object94 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(253)"));
        WebElement relatedObject9 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(254)"));
        actions.moveToElement(object94, 0, object94.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject9, 0, -relatedObject9.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.quit();
    }
}